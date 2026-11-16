from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from accounts.models import User
from catalog.models import Product
from orders.models import DirectPaymentEntry, Expense, Order, OrderItem
from orders.services.loyalty_service import annotate_customer_loyalty

ZERO = Decimal("0.00")


@dataclass(frozen=True)
class Period:
    start: datetime
    end: datetime
    label: str


def _aware_start(day: date):
    return timezone.make_aware(
        datetime.combine(day, time.min), timezone.get_current_timezone()
    )


def _aware_end(day: date):
    return timezone.make_aware(
        datetime.combine(day, time.max), timezone.get_current_timezone()
    )


def resolve_period(request) -> Period:
    """Resolve owner-selected period with strict bounded server-side parsing."""
    today = timezone.localdate()
    preset = (request.GET.get("period") or "month").strip().lower()[:16]

    if preset == "today":
        start_day = end_day = today
        label = "today"
    elif preset == "week":
        start_day = today - timedelta(days=6)
        end_day = today
        label = "week"
    elif preset == "year":
        start_day = date(today.year, 1, 1)
        end_day = today
        label = "year"
    elif preset == "custom":
        try:
            start_day = date.fromisoformat((request.GET.get("start") or "")[:10])
            end_day = date.fromisoformat((request.GET.get("end") or "")[:10])
        except ValueError:
            start_day = date(today.year, today.month, 1)
            end_day = today
            label = "month"
        else:
            # Prevent pathological or accidental huge reporting windows.
            if start_day > end_day:
                start_day, end_day = end_day, start_day
            earliest = today - timedelta(days=366 * 5)
            start_day = max(start_day, earliest)
            end_day = min(end_day, today)
            start_day = min(start_day, end_day)
            label = "custom"
    else:
        start_day = date(today.year, today.month, 1)
        end_day = today
        label = "month"

    return Period(_aware_start(start_day), _aware_end(end_day), label)


def build_accountant_report(request):
    period = resolve_period(request)

    # Realized figures require an actually delivered order and exclude a full refund.
    realized_orders = Order.objects.filter(
        delivered_at__range=(period.start, period.end),
        status=Order.Status.DELIVERED,
    ).exclude(payment_status=Order.PaymentStatus.REFUNDED)

    paid_orders = realized_orders.filter(payment_status=Order.PaymentStatus.PAID)

    sales = paid_orders.aggregate(v=Sum("grand_total"))["v"] or ZERO
    discounts = paid_orders.aggregate(v=Sum("discount_total"))["v"] or ZERO
    shipping = paid_orders.aggregate(v=Sum("shipping_total"))["v"] or ZERO

    items = OrderItem.objects.filter(order__in=paid_orders)
    snapshot_items = items.exclude(cost_total_snapshot__isnull=True)
    missing_cost_items = items.filter(cost_total_snapshot__isnull=True).count()
    cost = snapshot_items.aggregate(v=Sum("cost_total_snapshot"))["v"] or ZERO
    product_sales = items.aggregate(v=Sum("line_total"))["v"] or ZERO
    profit = product_sales - cost
    margin = (profit / product_sales * Decimal(100)) if product_sales > 0 else ZERO

    order_count = paid_orders.count()
    avg_order = (sales / order_count) if order_count else ZERO

    outstanding_orders = Order.objects.filter(
        created_at__range=(period.start, period.end),
        payment_status__in=[Order.PaymentStatus.UNPAID, Order.PaymentStatus.PENDING, Order.PaymentStatus.PARTIALLY_PAID],
    ).exclude(status__in=[Order.Status.CANCELLED, Order.Status.RETURNED])
    outstanding = outstanding_orders.aggregate(v=Sum("grand_total"))["v"] or ZERO
    # Deferred direct sales may have partial collections. Subtract only immutable
    # payment entries actually recorded against those still-open orders.
    deferred_collected = DirectPaymentEntry.objects.filter(
        order__in=outstanding_orders,
    ).aggregate(v=Sum("amount"))["v"] or ZERO
    outstanding = max(outstanding - deferred_collected, ZERO)

    refunded_count = Order.objects.filter(
        created_at__range=(period.start, period.end),
        payment_status__in=[Order.PaymentStatus.REFUNDED, Order.PaymentStatus.PARTIAL],
    ).count()

    expense_qs = Expense.objects.filter(
        status=Expense.Status.ACTIVE,
        incurred_on__range=(period.start.date(), period.end.date()),
    )
    expenses_total = expense_qs.aggregate(v=Sum("amount"))["v"] or ZERO
    expense_breakdown = dict.fromkeys((choice for choice, _ in Expense.Category.choices), ZERO)
    for row in expense_qs.values("category").annotate(total=Sum("amount")):
        expense_breakdown[row["category"]] = row["total"] or ZERO
    net_profit = profit - expenses_total
    net_margin = (
        (net_profit / product_sales * Decimal(100)) if product_sales > 0 else ZERO
    )

    legacy_delivered_without_timestamp = Order.objects.filter(
        status=Order.Status.DELIVERED,
        delivered_at__isnull=True,
    ).count()

    # Current inventory valuation is intentionally current-state, not historical.
    inventory_value = ZERO
    for product in Product.objects.exclude(status=Product.Status.ARCHIVED).only(
        "cost_price", "available_quantity"
    ):
        inventory_value += product.cost_price * product.available_quantity

    # Current loyalty distribution is lifetime-derived, independent of the
    # financial period selector.
    loyalty_customers = annotate_customer_loyalty(
        User.objects.filter(role=User.Role.CUSTOMER)
    )
    loyalty_counts = {
        "member": loyalty_customers.filter(eligible_order_count=0).count(),
        "new": loyalty_customers.filter(eligible_order_count=1).count(),
        "silver": loyalty_customers.filter(
            eligible_order_count__gte=2,
            eligible_order_count__lte=3,
        ).count(),
        "gold": loyalty_customers.filter(
            eligible_order_count__gte=4,
            eligible_order_count__lte=6,
        ).count(),
        "platinum": loyalty_customers.filter(
            eligible_order_count__gte=7,
            eligible_order_count__lte=9,
        ).count(),
        "royal": loyalty_customers.filter(eligible_order_count__gte=10).count(),
    }

    # Top products by realized profit using immutable snapshots.
    grouped = defaultdict(
        lambda: {
            "sku": "",
            "name_ar": "",
            "name_en": "",
            "sales": ZERO,
            "cost": ZERO,
            "quantity": 0,
            "missing_cost": False,
        }
    )
    for item in items.only(
        "sku", "name_ar", "name_en", "line_total", "cost_total_snapshot", "quantity"
    ):
        row = grouped[item.sku]
        row["sku"] = item.sku
        row["name_ar"] = item.name_ar
        row["name_en"] = item.name_en
        row["sales"] += item.line_total
        row["quantity"] += item.quantity
        if item.cost_total_snapshot is None:
            row["missing_cost"] = True
        else:
            row["cost"] += item.cost_total_snapshot

    top_products = []
    for row in grouped.values():
        row["profit_known"] = not row["missing_cost"]
        row["profit"] = row["sales"] - row["cost"] if row["profit_known"] else ZERO
        top_products.append(row)
    top_products.sort(
        key=lambda r: (r["profit"] is not None, r["profit"] or ZERO),
        reverse=True,
    )

    return {
        "period": period,
        "sales": sales,
        "product_sales": product_sales,
        "cost": cost,
        "profit": profit,
        "margin": margin,
        "discounts": discounts,
        "shipping": shipping,
        "order_count": order_count,
        "avg_order": avg_order,
        "outstanding": outstanding,
        "refunded_count": refunded_count,
        "expenses_total": expenses_total,
        "expense_breakdown": expense_breakdown,
        "net_profit": net_profit,
        "net_margin": net_margin,
        "inventory_value": inventory_value,
        "missing_cost_items": missing_cost_items,
        "legacy_delivered_without_timestamp": legacy_delivered_without_timestamp,
        "loyalty_counts": loyalty_counts,
        "top_products": top_products[:10],
    }

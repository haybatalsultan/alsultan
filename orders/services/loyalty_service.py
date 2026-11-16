from dataclasses import dataclass

from django.db.models import Count, Q

from orders.models import Order


@dataclass(frozen=True)
class LoyaltyStatus:
    code: str
    label_ar: str
    label_en: str
    eligible_orders: int
    next_threshold: int | None


# Central source of truth. The browser never supplies a loyalty tier.
# Minimum qualifying delivered orders for each tier:
# 0 MEMBER, 1 NEW, 2 SILVER, 4 GOLD, 7 PLATINUM, 10 ROYAL.
LOYALTY_TIERS = (
    (10, "ROYAL", "عميل ملكي", "Royal Customer", None),
    (7, "PLATINUM", "عميل بلاتيني", "Platinum Customer", 10),
    (4, "GOLD", "عميل ذهبي", "Gold Customer", 7),
    (2, "SILVER", "عميل فضي", "Silver Customer", 4),
    (1, "NEW", "عميل جديد", "New Customer", 2),
    (0, "MEMBER", "عميل", "Customer", 1),
)


def eligible_orders_for_user(user):
    if not getattr(user, "is_authenticated", False):
        return Order.objects.none()

    return Order.objects.filter(
        user=user,
        status=Order.Status.DELIVERED,
    ).exclude(payment_status=Order.PaymentStatus.REFUNDED)


def loyalty_status_from_count(count: int) -> LoyaltyStatus:
    safe_count = max(0, int(count or 0))
    for minimum, code, label_ar, label_en, next_threshold in LOYALTY_TIERS:
        if safe_count >= minimum:
            return LoyaltyStatus(
                code=code,
                label_ar=label_ar,
                label_en=label_en,
                eligible_orders=safe_count,
                next_threshold=next_threshold,
            )
    # Defensive fallback; the tuple above always covers zero.
    return LoyaltyStatus("MEMBER", "عميل", "Customer", safe_count, 1)


def loyalty_status_for_user(user) -> LoyaltyStatus:
    return loyalty_status_from_count(eligible_orders_for_user(user).count())


def annotate_customer_loyalty(queryset):
    """Annotate customer rows without N+1 queries.

    A delivered order stops qualifying if its payment was fully refunded.
    Returned orders are excluded because their status is no longer DELIVERED.
    """
    return queryset.annotate(
        eligible_order_count=Count(
            "orders",
            filter=Q(orders__status=Order.Status.DELIVERED)
            & ~Q(orders__payment_status=Order.PaymentStatus.REFUNDED),
            distinct=True,
        )
    )


def loyalty_label_from_count(count: int, language_code="ar"):
    status = loyalty_status_from_count(count)
    return status.label_en if language_code == "en" else status.label_ar

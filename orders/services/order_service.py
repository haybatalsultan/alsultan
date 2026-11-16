from decimal import ROUND_HALF_UP, Decimal
from secrets import token_hex

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from ambassadors.models import Redemption
from ambassadors.services.program import (
    available_points,
    consume_points,
    create_pending_referral,
    discount_for_points,
    ensure_profile,
    settings_obj,
)
from catalog.models import Product
from catalog.services.promotion_service import price_snapshot
from orders.models import (
    CheckoutReservationGuard,
    IdempotencyRecord,
    Order,
    OrderItem,
    OrderTimelineEvent,
    Reservation,
    ReservationLimitOverride,
)
from orders.services.inventory_service import reserve

MONEY = Decimal("0.01")


def money(v):
    return Decimal(v).quantize(MONEY, rounding=ROUND_HALF_UP)


def make_reference():
    return "HS-" + timezone.localdate().strftime("%y%m%d") + "-" + token_hex(3).upper()


POLICY_VERSION = "1.0-2026-08-14"


def _reservation_identity_key(user, customer):
    import hashlib

    if user and getattr(user, "is_authenticated", False):
        return f"user:{user.pk}"
    phone = "".join(
        ch for ch in str(customer.get("customer_phone", "")) if ch.isdigit()
    )
    return "guest:" + hashlib.sha256(phone.encode("utf-8")).hexdigest()[:64]


def _active_reserved_units(user, customer, now):
    from django.db.models import Sum

    qs = Reservation.objects.filter(
        released_at__isnull=True, consumed_at__isnull=True, expires_at__gt=now
    )
    if user and getattr(user, "is_authenticated", False):
        qs = qs.filter(order__user=user)
    else:
        qs = qs.filter(
            order__user__isnull=True,
            order__customer_phone=customer.get("customer_phone", ""),
        )
    return qs.aggregate(total=Sum("quantity"))["total"] or 0


@transaction.atomic
def create_order_from_cart(*, cart, customer, user=None, idempotency_key=""):
    if not idempotency_key or len(idempotency_key) > 100:
        raise ValueError("Invalid idempotency key.")
    customer = dict(customer)
    accepted = customer.pop("policy_acceptance", False)
    ambassador_code = customer.pop("ambassador_code", "")
    ambassador_discount_points = int(customer.pop("ambassador_discount_points", 0) or 0)
    if accepted is not True:
        raise ValueError("Policy acceptance is required.")

    existing = (
        IdempotencyRecord.objects.filter(key=idempotency_key)
        .select_related("order")
        .first()
    )
    if existing:
        return existing.order

    items = list(
        cart.items.select_related("product", "product__category")
        .prefetch_related("product__images")
        .select_for_update(of=("self", "product"))
    )
    if not items:
        raise ValueError("Cart is empty.")

    # Recalculate every price and promotion server-side while products are
    # locked. Browser/cart values are never trusted as sale prices.
    snapshots = {}
    subtotal = Decimal("0.00")
    base_subtotal = Decimal("0.00")
    now = timezone.now()
    total_units = sum(ci.quantity for ci in items)
    default_limit = max(
        1, min(int(getattr(settings, "CHECKOUT_RESERVATION_MAX_ITEMS", 3)), 20)
    )
    allowed_limit = default_limit
    if user and getattr(user, "is_authenticated", False):
        override = (
            ReservationLimitOverride.objects.filter(user=user, expires_at__gt=now)
            .order_by("-expires_at")
            .first()
        )
        if override:
            allowed_limit = max(
                default_limit,
                min(
                    override.max_items,
                    int(getattr(settings, "CHECKOUT_RESERVATION_OVERRIDE_MAX", 10)),
                ),
            )
    if total_units > allowed_limit:
        raise ValueError(f"CHECKOUT_LIMIT:{allowed_limit}")

    # Lock a stable reservation principal so the same customer cannot bypass the
    # limit by opening multiple browser sessions/tabs concurrently. Guest identity
    # is a one-way hash of the checkout phone; authenticated users use their account.
    identity_key = _reservation_identity_key(user, customer)
    guard, _ = CheckoutReservationGuard.objects.get_or_create(identity_key=identity_key)
    CheckoutReservationGuard.objects.select_for_update().get(pk=guard.pk)
    active_units = _active_reserved_units(user, customer, now)
    if active_units + total_units > allowed_limit:
        raise ValueError(f"CHECKOUT_LIMIT:{allowed_limit}")

    # Real reservation starts here, not at Add-to-Cart. Product rows are locked by
    # the surrounding atomic transaction so two checkouts cannot reserve the same unit.
    locked_products = {}
    for ci in items:
        product = Product.objects.select_for_update().get(pk=ci.product_id)
        locked_products[product.pk] = product
        if (
            product.status not in {product.Status.AVAILABLE, product.Status.RESERVED}
            or product.free_quantity < ci.quantity
        ):
            raise ValueError(f"{product.sku} is unavailable.")
        reserve(product.pk, ci.quantity, "CHECKOUT-PENDING", user)
        product.refresh_from_db(
            fields=["available_quantity", "reserved_quantity", "status"]
        )
        ci.product = product
        snap = price_snapshot(product)
        snapshots[product.pk] = snap
        subtotal += snap["final_price"] * ci.quantity
        base_subtotal += snap["base_price"] * ci.quantity

    sale_subtotal = money(subtotal)
    base_subtotal = money(base_subtotal)
    discount = money(base_subtotal - sale_subtotal)
    shipping = money(settings.STORE_SHIPPING_FEE)
    ambassador_discount = Decimal("0.00")
    redemption_profile = None
    if ambassador_discount_points:
        cfg = settings_obj()
        if not cfg.enabled:
            raise ValueError("برنامج سفير هيبة السلطان متوقف حاليًا.")
        if not user or not getattr(user, "is_authenticated", False):
            raise ValueError("يجب تسجيل الدخول لاستخدام نقاط سفير هيبة السلطان.")
        if ambassador_discount_points % cfg.redeem_points_block != 0:
            raise ValueError("يجب استخدام نقاط السفير بمضاعفات 1000 نقطة.")
        redemption_profile = ensure_profile(user)
        if available_points(redemption_profile) < ambassador_discount_points:
            raise ValueError("رصيد نقاط سفير هيبة السلطان غير كافٍ.")
        ambassador_discount = money(
            discount_for_points(ambassador_discount_points, cfg)
        )
        if ambassador_discount <= 0:
            raise ValueError("عدد النقاط المحدد لا ينتج خصمًا صالحًا.")
        if ambassador_discount > sale_subtotal:
            raise ValueError(
                "قيمة خصم نقاط السفير تتجاوز قيمة المنتجات في السلة. استخدم عددًا أقل من النقاط."
            )
    discount = money(discount + ambassador_discount)
    taxable_subtotal = money(sale_subtotal - ambassador_discount)
    tax = money(taxable_subtotal * settings.STORE_TAX_RATE / Decimal(100))
    grand = money(taxable_subtotal + tax + shipping)

    for _ in range(5):
        try:
            order = Order.objects.create(
                reference=make_reference(),
                user=user,
                subtotal=base_subtotal,
                discount_total=discount,
                tax_total=tax,
                shipping_total=shipping,
                grand_total=grand,
                policy_version=POLICY_VERSION,
                policy_accepted_at=timezone.now(),
                **customer,
            )
            break
        except IntegrityError:
            continue
    else:
        raise RuntimeError("Unable to create unique order reference.")

    if ambassador_code:
        create_pending_referral(order=order, code=ambassador_code, buyer=user)

    if ambassador_discount_points:
        redemption = Redemption.objects.create(
            profile=redemption_profile,
            kind=Redemption.Kind.DISCOUNT,
            points_used=ambassador_discount_points,
            amount_aed=ambassador_discount,
            order=order,
            status=Redemption.Status.APPLIED,
            resolved_at=timezone.now(),
            note=f"Checkout discount on {order.reference}",
        )
        consume_points(
            redemption_profile, ambassador_discount_points, redemption=redemption
        )

    # Successful order creation transfers the cart reservation into an order
    # reservation and starts the configured payment-step inventory window once. Refreshing pages
    # does not extend it. Provider-specific payment windows are tracked separately
    # on PaymentAttempt and never rewrite the original reservation deadline.
    order_reservation_expires = timezone.now() + timezone.timedelta(
        minutes=max(1, min(int(getattr(settings, "RESERVATION_MINUTES", 10)), 60))
    )
    for ci in items:
        product = ci.product
        snap = snapshots[product.pk]
        unit = money(snap["final_price"])
        base_unit = money(snap["base_price"])
        line = money(unit * ci.quantity)
        promo = snap.get("promotion")
        primary = next((img for img in product.images.all() if img.is_primary), None)
        OrderItem.objects.create(
            order=order,
            product=product,
            product_reference=product.product_reference,
            sku=product.sku,
            name_ar=product.name_ar,
            name_en=product.name_en,
            base_unit_price=base_unit,
            unit_price=unit,
            discount=money((base_unit - unit) * ci.quantity),
            promotion_label=(promo.name_ar if promo else "")[:180],
            gift_label=(snap.get("gift_ar") or snap.get("gift_en") or "")[:180],
            quantity=ci.quantity,
            line_total=line,
            cost_unit_snapshot=money(product.cost_price),
            cost_total_snapshot=money(product.cost_price * ci.quantity),
            image_url_snapshot=(primary.secure_url if primary else "")[:700],
            image_public_id_snapshot=(primary.cloudinary_public_id if primary else "")[
                :255
            ],
            verification_status_snapshot=product.verification_status,
            category_name_ar_snapshot=product.category.name_ar[:120],
            category_name_en_snapshot=product.category.name_en[:120],
            original_bead_count_snapshot=product.bead_count,
            requested_bead_count_snapshot=ci.requested_bead_count,
        )
        Reservation.objects.create(
            order=order,
            product=product,
            quantity=ci.quantity,
            expires_at=order_reservation_expires,
        )

    IdempotencyRecord.objects.create(user=user, key=idempotency_key, order=order)
    OrderTimelineEvent.objects.create(
        order=order,
        kind=OrderTimelineEvent.Kind.ORDER_CREATED,
        label_ar="تم إنشاء الطلب",
        label_en="Order created",
        actor=user,
        to_value=order.status,
    )
    cart.items.all().delete()
    cart.converted_at = timezone.now()
    cart.save(update_fields=["converted_at", "updated_at"])
    transaction.on_commit(
        lambda order_id=order.pk: __import__(
            "orders.services.notification_service", fromlist=["notify_order_created"]
        ).notify_order_created(order_id),
        robust=True,
    )
    return order

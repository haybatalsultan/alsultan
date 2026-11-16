from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from catalog.models import InventoryTransaction, Product
from catalog.services.promotion_service import price_snapshot
from orders.models import IdempotencyRecord, Order, OrderItem, OrderTimelineEvent
from orders.services.order_service import make_reference, money


class QuickSaleError(ValueError):
    pass


@transaction.atomic
def create_quick_sale(*, owner, cleaned_data):
    """Create one owner-only direct sale using server-authoritative product data."""
    key = f"quick-sale:{cleaned_data['idempotency_key']}"
    existing = (
        IdempotencyRecord.objects.select_related("order")
        .filter(key=key, user=owner)
        .first()
    )
    if existing:
        return existing.order, False

    submitted_product = cleaned_data["product"]
    product = (
        Product.objects.select_for_update()
        .select_related("category", "material")
        .prefetch_related("images")
        .get(pk=submitted_product.pk)
    )
    free_quantity = product.available_quantity - product.reserved_quantity
    if product.status != Product.Status.AVAILABLE or free_quantity < 1:
        raise QuickSaleError("The selected item is no longer available.")

    snap = price_snapshot(product)
    base_price = money(snap["base_price"])
    current_price = money(snap["final_price"])
    special_discount = money(cleaned_data.get("special_discount") or Decimal("0"))
    if special_discount < 0 or special_discount >= current_price:
        raise QuickSaleError("Special discount must be lower than the current sale price.")

    final_price = money(current_price - special_discount)
    promotion_discount = money(base_price - current_price)
    total_discount = money(promotion_discount + special_discount)
    tax_rate = Decimal(str(getattr(settings, "STORE_TAX_RATE", 0)))
    tax = money(final_price * tax_rate / Decimal("100"))
    grand_total = money(final_price + tax)
    now = timezone.now()
    is_deferred = cleaned_data["payment_method"] == Order.PaymentMethod.DEFERRED
    payment_status = Order.PaymentStatus.UNPAID if is_deferred else Order.PaymentStatus.PAID

    for _ in range(5):
        try:
            order = Order.objects.create(
                reference=make_reference(),
                user=None,
                customer_name=(cleaned_data.get("customer_name") or "Direct Customer")[:180],
                customer_email=(cleaned_data.get("customer_email") or "")[:254],
                customer_phone=(cleaned_data.get("customer_phone") or "")[:16],
                country="AE",
                area="Direct Sale",
                subtotal=base_price,
                discount_total=total_discount,
                tax_total=tax,
                shipping_total=Decimal("0.00"),
                grand_total=grand_total,
                currency="AED",
                status=Order.Status.DELIVERED,
                payment_status=payment_status,
                payment_method=cleaned_data["payment_method"],
                sale_channel=Order.SaleChannel.DIRECT,
                delivery_method=Order.DeliveryMethod.HAND_TO_HAND,
                hand_to_hand_at=now,
                hand_to_hand_by=owner,
                payment_due_date=cleaned_data.get("payment_due_date") if is_deferred else None,
                payment_reminder_days=cleaned_data.get("payment_reminder_days") or 3,
                additional_notes=(cleaned_data.get("deferred_note") or "")[:500],
                manual_paid_at=None if is_deferred else now,
                manual_paid_by=None if is_deferred else owner,
                delivered_at=now,
            )
            break
        except IntegrityError:
            continue
    else:
        raise RuntimeError("Unable to create a unique direct-sale reference.")

    primary = next((img for img in product.images.all() if img.is_primary), None)
    promo = snap.get("promotion")
    OrderItem.objects.create(
        order=order,
        product=product,
        product_reference=product.product_reference,
        sku=product.sku,
        name_ar=product.name_ar,
        name_en=product.name_en,
        base_unit_price=base_price,
        unit_price=final_price,
        discount=total_discount,
        promotion_label=(promo.name_ar if promo else "")[:180],
        gift_label=(snap.get("gift_ar") or snap.get("gift_en") or "")[:180],
        tax=tax,
        quantity=1,
        line_total=final_price,
        cost_unit_snapshot=money(product.cost_price),
        cost_total_snapshot=money(product.cost_price),
        image_url_snapshot=(primary.secure_url if primary else "")[:700],
        image_public_id_snapshot=(primary.cloudinary_public_id if primary else "")[:255],
        verification_status_snapshot=product.verification_status,
        category_name_ar_snapshot=product.category.name_ar[:120],
        category_name_en_snapshot=product.category.name_en[:120],
    )

    before = product.available_quantity
    product.available_quantity = before - 1
    if product.available_quantity == 0:
        product.status = Product.Status.SOLD
    elif product.reserved_quantity >= product.available_quantity:
        product.status = Product.Status.RESERVED
    else:
        product.status = Product.Status.AVAILABLE
    product.save(update_fields=["available_quantity", "status", "updated_at"])
    if product.status == Product.Status.SOLD:
        product_id = product.pk
        transaction.on_commit(
            lambda: __import__(
                "orders.services.cart_service",
                fromlist=["invalidate_product_from_carts"],
            ).invalidate_product_from_carts(product_id),
            robust=True,
        )

    InventoryTransaction.objects.create(
        product=product,
        movement_type=InventoryTransaction.Type.SALE,
        quantity=-1,
        before_quantity=before,
        after_quantity=product.available_quantity,
        order_reference=order.reference,
        actor=owner,
        reason="Owner direct sale",
    )

    try:
        IdempotencyRecord.objects.create(user=owner, key=key, order=order)
    except IntegrityError:
        # A concurrent duplicate request cannot be allowed to commit a second sale.
        raise QuickSaleError("This direct-sale request was already processed.")

    OrderTimelineEvent.objects.create(
        order=order,
        kind=OrderTimelineEvent.Kind.ORDER_CREATED,
        label_ar="تم تسجيل بيع مباشر وتسليم القطعة يدًا بيد بواسطة المالك",
        label_en="Owner direct sale recorded with hand-to-hand delivery",
        actor=owner,
        to_value=Order.Status.DELIVERED,
    )
    OrderTimelineEvent.objects.create(
        order=order,
        kind=OrderTimelineEvent.Kind.PAYMENT_CHANGED,
        label_ar=("تم تسجيل البيع كدفعة مؤجلة" if is_deferred else "تم تأكيد استلام مبلغ البيع المباشر"),
        label_en=("Direct sale recorded as deferred payment" if is_deferred else "Direct-sale payment confirmed"),
        actor=owner,
        from_value=Order.PaymentStatus.UNPAID,
        to_value=payment_status,
    )
    return order, True

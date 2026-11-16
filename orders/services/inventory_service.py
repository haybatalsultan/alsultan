from django.db import transaction
from django.utils import timezone

from catalog.models import InventoryTransaction, Product


@transaction.atomic
def reserve(product_id, quantity, order_reference, actor=None):
    p = Product.objects.select_for_update().get(pk=product_id)
    free = p.available_quantity - p.reserved_quantity
    if (
        quantity < 1
        or free < quantity
        or p.status not in {Product.Status.AVAILABLE, Product.Status.RESERVED}
    ):
        raise ValueError("Insufficient inventory.")
    before = p.reserved_quantity
    p.reserved_quantity += quantity
    if p.reserved_quantity >= p.available_quantity:
        p.status = Product.Status.RESERVED
    p.save(update_fields=["reserved_quantity", "status", "updated_at"])
    InventoryTransaction.objects.create(
        product=p,
        movement_type=InventoryTransaction.Type.RESERVE,
        quantity=quantity,
        before_quantity=before,
        after_quantity=p.reserved_quantity,
        order_reference=order_reference,
        actor=actor,
    )
    return p


@transaction.atomic
def release(
    product_id, quantity, order_reference, actor=None, reason="Reservation released"
):
    p = Product.objects.select_for_update().get(pk=product_id)
    before = p.reserved_quantity
    p.reserved_quantity = max(0, p.reserved_quantity - quantity)
    if (
        p.status == Product.Status.RESERVED
        and p.available_quantity > p.reserved_quantity
    ):
        p.status = Product.Status.AVAILABLE
    p.save(update_fields=["reserved_quantity", "status", "updated_at"])
    InventoryTransaction.objects.create(
        product=p,
        movement_type=InventoryTransaction.Type.RELEASE,
        quantity=quantity,
        before_quantity=before,
        after_quantity=p.reserved_quantity,
        order_reference=order_reference,
        actor=actor,
        reason=reason,
    )
    return p


@transaction.atomic
def consume_reservation(product_id, quantity, order_reference, actor=None):
    """Convert reserved stock into a sale exactly once under a row lock."""
    p = Product.objects.select_for_update().get(pk=product_id)
    if (
        quantity < 1
        or p.reserved_quantity < quantity
        or p.available_quantity < quantity
    ):
        raise ValueError("Reserved inventory is no longer available for sale.")
    before = p.available_quantity
    p.available_quantity -= quantity
    p.reserved_quantity -= quantity
    if p.available_quantity == 0:
        p.status = Product.Status.SOLD
    elif p.reserved_quantity >= p.available_quantity:
        p.status = Product.Status.RESERVED
    else:
        p.status = Product.Status.AVAILABLE
    p.save(
        update_fields=[
            "available_quantity",
            "reserved_quantity",
            "status",
            "updated_at",
        ]
    )
    if p.status == Product.Status.SOLD:
        product_id = p.pk
        transaction.on_commit(
            lambda: __import__(
                "orders.services.cart_service",
                fromlist=["invalidate_product_from_carts"],
            ).invalidate_product_from_carts(product_id),
            robust=True,
        )
    InventoryTransaction.objects.create(
        product=p,
        movement_type=InventoryTransaction.Type.SALE,
        quantity=-quantity,
        before_quantity=before,
        after_quantity=p.available_quantity,
        order_reference=order_reference,
        actor=actor,
        reason="Confirmed order sale",
    )
    return p


@transaction.atomic
def consume_order_reservations(order, actor=None):
    """Idempotently convert all active reservations for an order into sales."""
    from orders.models import Reservation

    rows = list(
        Reservation.objects.select_for_update()
        .filter(order=order)
        .select_related("product")
    )
    now = timezone.now()
    for r in rows:
        if r.consumed_at is not None:
            continue
        if r.released_at is not None:
            raise ValueError(
                "Order reservation was already released; inventory requires manual review."
            )
        consume_reservation(r.product_id, r.quantity, order.reference, actor)
        r.consumed_at = now
        r.save(update_fields=["consumed_at"])
    return len(rows)


@transaction.atomic
def release_order_reservations(order, actor=None, reason="Order cancelled"):
    """Idempotently release all active reservations for an unpaid/cancelled order."""
    from orders.models import Reservation

    rows = list(
        Reservation.objects.select_for_update()
        .filter(order=order)
        .select_related("product")
    )
    now = timezone.now()
    released = 0
    for r in rows:
        if r.consumed_at is not None:
            raise ValueError("Consumed inventory cannot be released as a reservation.")
        if r.released_at is not None:
            continue
        release(r.product_id, r.quantity, order.reference, actor=actor, reason=reason)
        r.released_at = now
        r.save(update_fields=["released_at"])
        released += 1
    return released

from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from catalog.models import Product
from orders.models import Cart, CartItem

from .inventory_service import release

MAX_CART_ITEM_QUANTITY = 10


def _reservation_minutes():
    # Bound configuration defensively. The browser never controls this value.
    return max(1, min(int(getattr(settings, "RESERVATION_MINUTES", 10)), 1440))


def _new_deadline():
    return timezone.now() + timezone.timedelta(minutes=_reservation_minutes())


def _cart_reference(cart):
    return f"CART-{cart.public_id.hex[:16]}"


def touch(cart):
    now = timezone.now()
    Cart.objects.filter(pk=cart.pk).update(updated_at=now)
    cart.updated_at = now


@transaction.atomic
def _ensure_legacy_cart_reservations(cart):
    # Upgrade safety: release any v20.12 cart-level holds once, then make the cart informational.
    rows = list(
        CartItem.objects.select_for_update()
        .filter(cart=cart, reserved_until__isnull=False)
        .select_related("product")
    )
    for item in rows:
        product = Product.objects.select_for_update().get(pk=item.product_id)
        if product.reserved_quantity > 0:
            release(
                product.pk,
                min(item.quantity, product.reserved_quantity),
                _cart_reference(cart),
                actor=cart.user,
                reason="v20.13 anti-hoarding cart migration",
            )
        item.reserved_until = None
        item.save(update_fields=["reserved_until", "updated_at"])


def purge_abandoned_cart_items(*, cart=None, limit=500):
    """Delete informational cart rows that have been untouched past retention.

    This is housekeeping only: cart rows never reserve inventory. The bound and
    optional cart scope keep request-path work predictable.
    """
    days = max(1, min(int(getattr(settings, "CART_ITEM_RETENTION_DAYS", 30)), 365))
    cutoff = timezone.now() - timezone.timedelta(days=days)
    qs = CartItem.objects.filter(updated_at__lt=cutoff)
    if cart is not None:
        qs = qs.filter(cart=cart)
    ids = list(qs.order_by("updated_at").values_list("pk", flat=True)[:limit])
    if not ids:
        return 0
    deleted, _ = CartItem.objects.filter(pk__in=ids).delete()
    return deleted


def get_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        if not cart.contact_phone and getattr(request.user, "phone_e164", ""):
            cart.contact_phone = request.user.phone_e164
            cart.save(update_fields=["contact_phone", "updated_at"])
        _ensure_legacy_cart_reservations(cart)
        purge_expired_cart_items(cart=cart, limit=100)
        purge_abandoned_cart_items(cart=cart, limit=100)
        return cart
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(
        user=None, session_key=request.session.session_key
    )
    _ensure_legacy_cart_reservations(cart)
    purge_expired_cart_items(cart=cart, limit=100)
    purge_abandoned_cart_items(cart=cart, limit=100)
    return cart


def _parse_quantity(quantity):
    try:
        quantity = int(quantity)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid quantity.") from exc
    if quantity < 1 or quantity > MAX_CART_ITEM_QUANTITY:
        raise ValueError("Invalid quantity.")
    return quantity


def _snapshot(product):
    primary = product.images.filter(is_primary=True).only("secure_url").first()
    return {
        "snapshot_name_ar": product.name_ar,
        "snapshot_name_en": product.name_en,
        "snapshot_unit_price": product.effective_price,
        "snapshot_image_url": primary.secure_url if primary else "",
        "snapshot_verification_status": product.verification_status,
    }


@transaction.atomic
def add(cart, product, quantity=1):
    quantity = _parse_quantity(quantity)
    locked_product = Product.objects.select_for_update().get(pk=product.pk)
    if (
        locked_product.status not in {Product.Status.AVAILABLE, Product.Status.RESERVED}
        or locked_product.free_quantity < 1
    ):
        raise ValueError("Product is unavailable.")
    item = (
        CartItem.objects.select_for_update()
        .filter(cart=cart, product=locked_product)
        .first()
    )
    snapshot = _snapshot(locked_product)
    new_quantity = (item.quantity if item else 0) + quantity
    if (
        new_quantity > MAX_CART_ITEM_QUANTITY
        or new_quantity > locked_product.free_quantity
    ):
        raise ValueError("Requested quantity is unavailable.")
    if item:
        item.quantity = new_quantity
        item.reserved_until = None
        for field, value in snapshot.items():
            setattr(item, field, value)
        item.save(
            update_fields=["quantity", "reserved_until", *snapshot.keys(), "updated_at"]
        )
    else:
        item = CartItem.objects.create(
            cart=cart,
            product=locked_product,
            quantity=quantity,
            reserved_until=None,
            **snapshot,
        )
    touch(cart)
    return item


@transaction.atomic
def set_quantity(cart, item_id, quantity):
    quantity = _parse_quantity(quantity)
    item = (
        CartItem.objects.select_for_update()
        .select_related("product")
        .get(pk=item_id, cart=cart)
    )
    product = Product.objects.select_for_update().get(pk=item.product_id)
    if (
        product.status not in {Product.Status.AVAILABLE, Product.Status.RESERVED}
        or quantity > product.free_quantity
    ):
        raise ValueError("Requested quantity is unavailable.")
    item.quantity = quantity
    item.reserved_until = None
    item.save(update_fields=["quantity", "reserved_until", "updated_at"])
    touch(cart)
    return item


@transaction.atomic
def remove(cart, item_id, *, reason="Removed from cart"):
    item = (
        CartItem.objects.select_for_update()
        .select_related("product")
        .get(pk=item_id, cart=cart)
    )
    snapshot = {
        "product_reference": item.product.product_reference,
        "quantity": item.quantity,
    }
    item.delete()
    touch(cart)
    return snapshot


def purge_expired_cart_items(*, cart=None, limit=200):
    # No cart-level inventory holds in v20.13. Kept as a compatibility no-op.
    # Keep the historical keyword parameters because callers still pass them.
    del cart, limit
    return 0


def expire_item_if_due(cart, item_id):
    # Compatibility no-op: item-level expiry is retained in the public service API.
    del cart, item_id
    return False, 0


def totals(cart):
    subtotal = Decimal("0.00")
    for item in cart.items.select_related("product"):
        subtotal += item.product.effective_price * item.quantity
    return {"subtotal": subtotal, "grand_total": subtotal}


@transaction.atomic
def sanitize_cart(cart):
    """Remove permanently unavailable items from a cart.

    Reserved-by-another-checkout items are intentionally kept because they may
    become available again when that checkout expires. SOLD/ARCHIVED/DRAFT or
    zero-stock products are stale and are removed server-side.
    """
    removed = []
    rows = list(
        CartItem.objects.select_for_update().filter(cart=cart).select_related("product")
    )
    for item in rows:
        product = Product.objects.select_for_update().get(pk=item.product_id)
        permanently_unavailable = (
            product.status
            in {Product.Status.SOLD, Product.Status.ARCHIVED, Product.Status.DRAFT}
            or product.available_quantity <= 0
        )
        if permanently_unavailable:
            removed.append(
                {
                    "sku": product.sku or product.product_reference,
                    "name_ar": product.name_ar,
                    "name_en": product.name_en,
                }
            )
            item.delete()
    if removed:
        touch(cart)
    return removed


def invalidate_product_from_carts(product_id):
    """Delete a sold product from every remaining cart after the sale commits."""
    CartItem.objects.filter(product_id=product_id).delete()

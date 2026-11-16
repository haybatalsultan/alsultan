from django.conf import settings
from django.db.models import Sum


def _cart_item_count(request):
    # Read-only header count: do not create a cart merely by rendering a page.
    from orders.models import Cart

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).only("pk").first()
    else:
        session_key = request.session.session_key
        cart = (
            Cart.objects.filter(user=None, session_key=session_key).only("pk").first()
            if session_key
            else None
        )
    if not cart:
        return 0
    return (
        cart.items.filter(
            product__status__in=["AVAILABLE", "RESERVED"],
            product__available_quantity__gt=0,
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )


def _wishlist_item_count(request):
    # Read-only count for authenticated users only. The server remains the
    # source of truth; client-side UI mirrors this value after POST updates.
    if not request.user.is_authenticated:
        return 0
    from catalog.models import WishlistItem

    return WishlistItem.objects.filter(user=request.user).count()


def _active_tracking_context(request):
    if (
        not request.user.is_authenticated
        or getattr(request.user, "role", "") != "CUSTOMER"
    ):
        return {"ACTIVE_TRACKING_URL": "", "ACTIVE_TRACKING_STATUS": ""}
    from django.urls import reverse

    from orders.models import Order

    active = list(
        Order.objects.filter(user=request.user)
        .exclude(
            status__in=[
                Order.Status.DELIVERED,
                Order.Status.CANCELLED,
                Order.Status.RETURNED,
            ]
        )
        .only("public_id", "status")
        .order_by("-created_at")[:2]
    )
    if not active:
        return {"ACTIVE_TRACKING_URL": "", "ACTIVE_TRACKING_STATUS": ""}
    if len(active) == 1:
        return {
            "ACTIVE_TRACKING_URL": reverse(
                "orders:detail", kwargs={"public_id": active[0].public_id}
            ),
            "ACTIVE_TRACKING_STATUS": active[0].status,
        }
    return {
        "ACTIVE_TRACKING_URL": reverse("orders:my_orders"),
        "ACTIVE_TRACKING_STATUS": "MULTIPLE",
    }


def _management_context(request):
    """Read-only management shell context; never grants permissions."""
    is_management_path = request.path.startswith("/management/")
    if not is_management_path or not request.user.is_authenticated:
        return {
            "IS_MANAGEMENT_PATH": is_management_path,
            "MGMT_CAN_VIEW_ORDERS": False,
            "MGMT_CAN_VIEW_PRODUCTS": False,
            "MGMT_CAN_VIEW_CUSTOMERS": False,
            "MGMT_CAN_MANAGE_MASTER_DATA": False,
            "MGMT_CAN_VIEW_ABANDONED_CARTS": False,
            "MGMT_IS_OWNER": False,
        }
    from accounts.models import User
    from accounts.services.permission_service import can

    user = request.user
    return {
        "IS_MANAGEMENT_PATH": True,
        "MGMT_CAN_VIEW_ORDERS": can(user, "view_orders"),
        "MGMT_CAN_VIEW_PRODUCTS": can(user, "view_products"),
        "MGMT_CAN_VIEW_CUSTOMERS": can(user, "view_customers"),
        "MGMT_CAN_MANAGE_MASTER_DATA": can(user, "manage_master_data"),
        "MGMT_CAN_VIEW_ABANDONED_CARTS": can(user, "view_abandoned_carts"),
        "MGMT_IS_OWNER": user.role == User.Role.OWNER,
    }


def store_context(request):
    phone = settings.STORE_CONTACT_PHONE
    management = _management_context(request)
    is_management_path = management["IS_MANAGEMENT_PATH"]
    return {
        "STORE_NAME_AR": "هيبة السلطان",
        "STORE_NAME_EN": "Haybat Al Sultan",
        "STORE_CONTACT_PHONE": phone,
        "STORE_CONTACT_PHONE_DISPLAY": "+971 50 408 4006"
        if phone == "+971504084006"
        else phone,
        "STORE_CONTACT_PHONE_DIGITS": "".join(ch for ch in phone if ch.isdigit()),
        "STORE_WHATSAPP_DIGITS": "".join(
            ch for ch in settings.WHATSAPP_NUMBER if ch.isdigit()
        ),
        "STORE_CONTACT_EMAIL": settings.STORE_CONTACT_EMAIL,
        "STORE_SOCIAL_HANDLE": settings.STORE_SOCIAL_HANDLE,
        "GOOGLE_OAUTH_ENABLED": settings.GOOGLE_OAUTH_ENABLED,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
        "CART_ITEM_COUNT": 0 if is_management_path else _cart_item_count(request),
        "WISHLIST_ITEM_COUNT": 0
        if is_management_path
        else _wishlist_item_count(request),
        **(
            {"ACTIVE_TRACKING_URL": "", "ACTIVE_TRACKING_STATUS": ""}
            if is_management_path
            else _active_tracking_context(request)
        ),
        **management,
    }

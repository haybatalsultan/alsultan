from secrets import token_urlsafe
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from accounts.models import User
from accounts.services.permission_service import can
from ambassadors.services.program import available_points, ensure_profile, settings_obj
from catalog.models import Product
from core.models import StoreSetting
from core.services.audit_service import audit
from core.services.checkout_fields import sanitise_checkout_field_config
from core.services.payment_policy import current_payment_policy

from .forms import CartFollowUpForm, CheckoutForm, OrderTrackingForm
from .models import (
    CartItem,
    Order,
    OrderTimelineEvent,
    PaymentAttempt,
    ReservationLimitOverride,
    ReservationLimitRequest,
)
from .services.cart_service import (
    add,
    expire_item_if_due,
    get_cart,
    purge_expired_cart_items,
    remove,
    sanitize_cart,
    set_quantity,
    totals,
)
from .services.notification_service import notify_reservation_limit_request
from .services.order_service import create_order_from_cart
from .services.reservation_service import (
    expire_unpaid_order_if_needed,
    reservation_deadline,
)
from .services.stripe_service import create_checkout_session, reconcile_order_payment
from .services.whatsapp_service import whatsapp_url


ORDERS_CART_URL = 'orders:cart'
ORDERS_CONFIRMATION_URL = 'orders:confirmation'
ORDERS_DETAIL_URL = 'orders:detail'

def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _cart_error_message(exc, language_code):
    """Translate known cart validation failures without exposing internals."""
    message = str(exc)
    unavailable = {
        "Product is unavailable.",
        "Requested quantity is unavailable.",
    }
    invalid = {"Invalid quantity."}
    expired = {"Cart reservation expired."}
    is_en = language_code == "en"
    if message in unavailable:
        return (
            "This item is currently unavailable or temporarily reserved by another checkout."
            if is_en
            else "عذرًا، هذه القطعة غير متاحة حاليًا أو محجوزة مؤقتًا لعملية إتمام طلب أخرى."
        )
    if message in invalid:
        return "Please choose a valid quantity." if is_en else "يرجى اختيار كمية صحيحة."
    if message in expired:
        return (
            "Your reservation expired and the item was removed from the cart."
            if is_en
            else "انتهت مدة حجز القطعة وتمت إزالتها من السلة."
        )
    if message.startswith("CHECKOUT_LIMIT:"):
        limit = message.split(":", 1)[1]
        return (
            f"Checkout reservation is limited to {limit} items. Contact the store for a temporary increase."
            if is_en
            else f"الحد الحالي لحجز إتمام الطلب هو {limit} قطع. تواصل مع الإدارة لرفع الحد مؤقتًا."
        )
    return (
        "Unable to update the cart."
        if is_en
        else "تعذر تحديث السلة. يرجى المحاولة مرة أخرى."
    )


def _cart_payload(cart, *, item=None):
    purge_expired_cart_items(cart=cart, limit=100)
    current_totals = totals(cart)
    payload = {
        "ok": True,
        "cart_count": sum(cart.items.values_list("quantity", flat=True)),
        "grand_total": str(current_totals["grand_total"]),
        "cart_empty": not cart.items.exists(),
    }
    if item is not None:
        product = Product.objects.prefetch_related("images").get(pk=item.product_id)
        primary = product.images.filter(is_primary=True).only("secure_url").first()
        # v20.13 carts are informational only: Add-to-Cart does not reserve stock.
        # For UI semantics, free_quantity is therefore the total quantity this cart
        # may hold for this product, not an inventory reservation balance.
        cart_available_quantity = max(0, product.free_quantity)
        payload.update(
            {
                "item_id": item.id,
                "quantity": item.quantity,
                "unit_price": str(product.effective_price),
                "line_total": str(product.effective_price * item.quantity),
                "product_name_ar": product.name_ar,
                "product_name_en": product.name_en,
                "product_sku": product.sku,
                "image_url": primary.secure_url if primary else "",
                "free_quantity": cart_available_quantity,
                "cart_item_quantity": item.quantity,
                "stock_limit_reached": item.quantity >= cart_available_quantity,
                "reserved_until": (
                    item.reserved_until.isoformat() if item.reserved_until else ""
                ),
            }
        )
    return payload


def _configure_ambassador_checkout_fields(form, request, program):
    if not program.enabled:
        form.fields.pop("ambassador_code", None)
        form.fields.pop("ambassador_discount_points", None)
        return form
    if not (
        request.user.is_authenticated
        and getattr(request.user, "role", "") == "CUSTOMER"
    ):
        form.fields.pop("ambassador_discount_points", None)
    return form


def _checkout_conflicts(cart):
    """Return current cart lines that cannot enter checkout.

    This is an early UX guard only. create_order_from_cart repeats the same
    availability decision under row locks, so a race between GET and POST cannot
    create an oversell. No competing customer/order information is exposed.
    """
    conflicts = []
    rows = cart.items.select_related("product").order_by("pk")
    for item in rows:
        product = item.product
        if (
            product.status
            in {Product.Status.SOLD, Product.Status.ARCHIVED, Product.Status.DRAFT}
            or product.available_quantity <= 0
        ):
            kind = "sold"
        elif product.free_quantity < item.quantity:
            kind = "reserved"
        else:
            continue
        conflicts.append(
            {
                "sku": product.sku or product.product_reference,
                "name_ar": product.name_ar,
                "name_en": product.name_en,
                "kind": kind,
            }
        )
    return conflicts


def _reconcile_customer_expired_orders(user, limit=20):
    """Reconcile only this customer's expired unpaid holds before rendering."""
    now = timezone.now()
    ids = list(
        Order.objects.filter(
            user=user,
            payment_status__in=[
                Order.PaymentStatus.UNPAID,
                Order.PaymentStatus.PENDING,
                Order.PaymentStatus.FAILED,
            ],
            reservations__released_at__isnull=True,
            reservations__consumed_at__isnull=True,
            reservations__expires_at__lte=now,
        )
        .exclude(
            status__in=[
                Order.Status.CANCELLED,
                Order.Status.RETURNED,
                Order.Status.DELIVERED,
            ]
        )
        .order_by("reservations__expires_at")
        .values_list("pk", flat=True)
        .distinct()[:limit]
    )
    for order_id in ids:
        expire_unpaid_order_if_needed(order_id)


def _can_access_order(request, order):
    return (
        request.user.is_authenticated and order.user_id == request.user.id
    ) or request.session.get("recent_order") == str(order.public_id)


def _is_management_user(request):
    return request.user.is_authenticated and request.user.role in {
        User.Role.OWNER,
        User.Role.SUPERVISOR,
    }


def _management_order_redirect(request, public_id):
    """Keep management identities on the MFA-protected management surface."""
    if not _is_management_user(request):
        return None
    if can(request.user, "view_orders"):
        return redirect("core:management_order", public_id=public_id)
    return render(request, "orders/order_access_denied.html", status=403)


def _order_not_available(request):
    """Branded non-enumerating 404 for customer order surfaces."""
    return render(request, "orders/order_not_available.html", status=404)


@require_GET
def cart_view(request):
    cart = get_cart(request)
    removed = sanitize_cart(cart)
    if removed:
        labels = ", ".join(x["sku"] for x in removed)
        messages.warning(
            request,
            (
                f"The following sold/unavailable items were removed from your cart: {labels}"
                if request.LANGUAGE_CODE == "en"
                else f"تمت إزالة القطع المباعة أو غير المتاحة من سلتك: {labels}"
            ),
        )
    follow_up_form = CartFollowUpForm(initial={"phone": cart.contact_phone})
    cart_items = list(
        cart.items.select_related("product")
        .prefetch_related("product__images")
        .order_by("-created_at")
    )
    now = timezone.now()
    cart_count = sum(item.quantity for item in cart_items)
    default_limit = max(
        1, min(int(getattr(settings, "CHECKOUT_RESERVATION_MAX_ITEMS", 3)), 20)
    )
    override = None
    pending_limit_request = None
    if (
        request.user.is_authenticated
        and getattr(request.user, "role", "") == "CUSTOMER"
    ):
        override = (
            ReservationLimitOverride.objects.filter(
                user=request.user, expires_at__gt=now
            )
            .order_by("-expires_at")
            .first()
        )
        pending_limit_request = (
            ReservationLimitRequest.objects.filter(
                user=request.user, status=ReservationLimitRequest.Status.PENDING
            )
            .order_by("-created_at")
            .first()
        )
    effective_limit = max(
        default_limit, override.max_items if override else default_limit
    )
    for item in cart_items:
        item.display_line_total = item.product.effective_price * item.quantity
        item.ui_max_quantity = max(
            1, min(10, max(item.quantity, item.product.free_quantity))
        )
        item.reservation_seconds_remaining = 0
    number = "".join(
        ch for ch in getattr(settings, "WHATSAPP_NUMBER", "") if ch.isdigit()
    )
    wa_text = (
        "السلام عليكم، أرغب في رفع حد الحجز المؤقت في متجر هيبة السلطان. "
        f"لدي {cart_count} قطع في السلة والحد الحالي {effective_limit} قطع. الرجاء مراجعة طلبي."
    )
    whatsapp_limit_url = (
        f"https://wa.me/{number}?{urlencode({'text': wa_text})}" if number else ""
    )
    bead_setting, _ = StoreSetting.objects.get_or_create(singleton=True)
    return render(
        request,
        "orders/cart.html",
        {
            "bead_adjustment_enabled": bead_setting.bead_adjustment_enabled,
            "cart": cart,
            "cart_items": cart_items,
            "totals": totals(cart),
            "follow_up_form": follow_up_form,
            "cart_count": cart_count,
            "default_reservation_limit": default_limit,
            "effective_reservation_limit": effective_limit,
            "active_reservation_override": override,
            "pending_limit_request": pending_limit_request,
            "over_checkout_limit": cart_count > effective_limit,
            "whatsapp_limit_url": whatsapp_limit_url,
        },
    )


@require_GET
def cart_status(request):
    cart = get_cart(request)
    current = (
        cart.items.filter(
            product__status__in=[Product.Status.AVAILABLE, Product.Status.RESERVED],
            product__available_quantity__gt=0,
        ).aggregate(
            total=__import__("django.db.models", fromlist=["Sum"]).Sum("quantity")
        )[
            "total"
        ]
        or 0
    )
    try:
        client_count = max(0, min(int(request.GET.get("count", current)), 999))
    except (TypeError, ValueError):
        client_count = current
    response = JsonResponse(
        {"ok": True, "cart_count": current, "changed": current != client_count}
    )
    response["Cache-Control"] = "no-store, private"
    return response


@login_required
@require_POST
def reservation_limit_request(request):
    if getattr(request.user, "role", "") != "CUSTOMER":
        raise Http404
    cart = get_cart(request)
    sanitize_cart(cart)
    cart_count = sum(cart.items.values_list("quantity", flat=True))
    default_limit = max(
        1, min(int(getattr(settings, "CHECKOUT_RESERVATION_MAX_ITEMS", 3)), 20)
    )
    max_cap = max(
        default_limit + 1,
        min(int(getattr(settings, "CHECKOUT_RESERVATION_OVERRIDE_MAX", 10)), 20),
    )
    if cart_count <= default_limit:
        messages.info(
            request,
            (
                "لا تحتاج السلة الحالية إلى رفع الحد."
                if request.LANGUAGE_CODE != "en"
                else "Your current cart does not require a higher limit."
            ),
        )
        return redirect(ORDERS_CART_URL)
    if cart_count > max_cap:
        messages.error(
            request,
            (
                f"الحد الأعلى للاستثناء هو {max_cap} قطع. تواصل مع الإدارة."
                if request.LANGUAGE_CODE != "en"
                else f"The maximum temporary exception is {max_cap} items. Please contact management."
            ),
        )
        return redirect(ORDERS_CART_URL)
    with transaction.atomic():
        pending = (
            ReservationLimitRequest.objects.select_for_update()
            .filter(user=request.user, status=ReservationLimitRequest.Status.PENDING)
            .order_by("-created_at")
            .first()
        )
        if pending:
            if pending.requested_items != cart_count:
                pending.requested_items = cart_count
                pending.cart = cart
                pending.admin_notified_at = None
                pending.save(
                    update_fields=[
                        "requested_items",
                        "cart",
                        "admin_notified_at",
                        "updated_at",
                    ]
                )
            req = pending
        else:
            req = ReservationLimitRequest.objects.create(
                user=request.user, cart=cart, requested_items=cart_count
            )
        transaction.on_commit(
            lambda: notify_reservation_limit_request(req.pk), robust=True
        )
    audit(
        request,
        "reservation_limit_requested",
        req,
        new={"requested_items": req.requested_items},
    )
    messages.success(
        request,
        (
            "تم إرسال طلب رفع الحد إلى إدارة هيبة السلطان. ستتم مراجعته قبل منح أي استثناء."
            if request.LANGUAGE_CODE != "en"
            else "Your temporary limit request was sent to Haybat Al Sultan management for review."
        ),
    )
    return redirect(ORDERS_CART_URL)


@require_POST
def cart_add(request, public_id):
    cart = get_cart(request)
    sanitize_cart(cart)
    product = get_object_or_404(
        Product, public_id=public_id, status=Product.Status.AVAILABLE
    )
    try:
        item = add(cart, product, request.POST.get("quantity", 1))
        audit(
            request,
            "cart_item_added",
            cart,
            new={
                "product_reference": product.product_reference,
                "quantity": item.quantity,
            },
        )
        if _is_ajax(request):
            return JsonResponse(_cart_payload(cart, item=item))
        messages.success(
            request,
            (
                "تمت إضافة المنتج إلى السلة."
                if request.LANGUAGE_CODE != "en"
                else "The item was added to your cart."
            ),
        )
    except (ValueError, TypeError) as exc:
        if _is_ajax(request):
            return JsonResponse(
                {
                    "ok": False,
                    "message": _cart_error_message(exc, request.LANGUAGE_CODE),
                },
                status=400,
            )
        messages.error(request, _cart_error_message(exc, request.LANGUAGE_CODE))
    return redirect(ORDERS_CART_URL)



@require_POST
def cart_bead_adjustment(request, item_id):
    cart = get_cart(request)
    sanitize_cart(cart)
    item = get_object_or_404(cart.items.select_related("product"), id=item_id)
    store, _ = StoreSetting.objects.get_or_create(singleton=True)
    product_count = item.product.bead_count
    if not store.bead_adjustment_enabled or not product_count or product_count <= 33:
        item.requested_bead_count = None
        item.save(update_fields=["requested_bead_count", "updated_at"])
        messages.error(request, "خدمة ضبط عدد الخرز غير متاحة لهذه القطعة.")
        return redirect(ORDERS_CART_URL)
    raw = (request.POST.get("requested_bead_count") or "").strip()
    if raw == "":
        requested = None
    else:
        try:
            requested = int(raw)
        except (TypeError, ValueError):
            requested = 0
        if requested < 33 or requested > product_count:
            messages.error(
                request,
                f"العدد المطلوب يجب أن يكون من 33 إلى {product_count} خرزة."
                if request.LANGUAGE_CODE != "en"
                else f"Requested bead count must be between 33 and {product_count}.",
            )
            return redirect(ORDERS_CART_URL)
        if requested == product_count:
            requested = None
    item.requested_bead_count = requested
    item.save(update_fields=["requested_bead_count", "updated_at"])
    audit(
        request,
        "cart_bead_adjustment_updated",
        item,
        new={
            "product_reference": item.product.product_reference,
            "original_bead_count": product_count,
            "requested_bead_count": requested,
        },
    )
    messages.success(
        request,
        "تم حفظ طلب ضبط عدد الخرز مجانًا." if requested else "تم الإبقاء على عدد الخرز الأصلي.",
    )
    return redirect(ORDERS_CART_URL)

@require_POST
def cart_remove(request, item_id):
    cart = get_cart(request)
    sanitize_cart(cart)
    item = get_object_or_404(cart.items.select_related("product"), id=item_id)
    snapshot = remove(cart, item.id)
    audit(
        request,
        "cart_item_removed",
        cart,
        old=snapshot,
        new={"removed": True},
    )
    if _is_ajax(request):
        return JsonResponse(_cart_payload(cart))
    return redirect(ORDERS_CART_URL)


@require_POST
def cart_quantity(request, item_id):
    cart = get_cart(request)
    sanitize_cart(cart)
    try:
        item = set_quantity(cart, item_id, request.POST.get("quantity"))
    except CartItem.DoesNotExist:
        raise Http404
    except (ValueError, TypeError) as exc:
        if _is_ajax(request):
            return JsonResponse(
                {
                    "ok": False,
                    "message": _cart_error_message(exc, request.LANGUAGE_CODE),
                },
                status=400,
            )
        messages.error(request, _cart_error_message(exc, request.LANGUAGE_CODE))
        return redirect(ORDERS_CART_URL)

    audit(
        request,
        "cart_item_quantity_changed",
        cart,
        new={
            "product_reference": item.product.product_reference,
            "quantity": item.quantity,
        },
    )
    if _is_ajax(request):
        return JsonResponse(_cart_payload(cart, item=item))
    return redirect(ORDERS_CART_URL)


@require_POST
def cart_expire(request, item_id):
    cart = get_cart(request)
    expired, remaining = expire_item_if_due(cart, item_id)
    payload = _cart_payload(cart)
    payload.update({"expired": expired, "remaining_seconds": max(0, remaining)})
    return JsonResponse(payload)


@require_POST
def cart_follow_up(request):
    cart = get_cart(request)
    if not cart.items.exists():
        return redirect(ORDERS_CART_URL)
    form = CartFollowUpForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "orders/cart.html",
            {"cart": cart, "totals": totals(cart), "follow_up_form": form},
            status=400,
        )
    cart.contact_phone = form.cleaned_data["phone"]
    cart.whatsapp_opt_in_at = timezone.now()
    cart.reminder_sent_at = None
    cart.save(
        update_fields=[
            "contact_phone",
            "whatsapp_opt_in_at",
            "reminder_sent_at",
            "updated_at",
        ]
    )
    audit(
        request,
        "cart_whatsapp_consent_enabled",
        cart,
        old={"whatsapp_opt_in": False},
        new={"whatsapp_opt_in": True},
    )
    messages.success(
        request,
        (
            "تم حفظ موافقتك. لن نرسل أكثر من تذكير واحد لهذه السلة."
            if request.LANGUAGE_CODE != "en"
            else "Your consent was saved. We will send no more than one reminder for this cart."
        ),
    )
    return redirect(ORDERS_CART_URL)


@require_POST
def cart_follow_up_cancel(request):
    cart = get_cart(request)
    cart.whatsapp_opt_in_at = None
    cart.reminder_sent_at = None
    if not request.user.is_authenticated:
        cart.contact_phone = ""
        fields = [
            "whatsapp_opt_in_at",
            "reminder_sent_at",
            "contact_phone",
            "updated_at",
        ]
    else:
        fields = ["whatsapp_opt_in_at", "reminder_sent_at", "updated_at"]
    cart.save(update_fields=fields)
    audit(
        request,
        "cart_whatsapp_consent_disabled",
        cart,
        old={"whatsapp_opt_in": True},
        new={"whatsapp_opt_in": False},
    )
    messages.success(
        request,
        (
            "تم إلغاء موافقة تذكير واتساب لهذه السلة."
            if request.LANGUAGE_CODE != "en"
            else "WhatsApp reminder consent was removed for this cart."
        ),
    )
    return redirect(ORDERS_CART_URL)


def checkout(request):
    cart = get_cart(request)
    removed = sanitize_cart(cart)
    if removed:
        labels = ", ".join(row["sku"] for row in removed)
        messages.warning(
            request,
            (
                f"The following sold/unavailable items were removed from your cart: {labels}"
                if request.LANGUAGE_CODE == "en"
                else f"تمت إزالة القطع المباعة أو غير المتاحة من سلتك: {labels}"
            ),
        )
    if not cart.items.exists():
        return redirect(ORDERS_CART_URL)
    conflicts = _checkout_conflicts(cart)
    if conflicts:
        reserved = [row["sku"] for row in conflicts if row["kind"] == "reserved"]
        sold = [row["sku"] for row in conflicts if row["kind"] == "sold"]
        if reserved:
            labels = ", ".join(reserved)
            messages.warning(
                request,
                (
                    f"{labels} is temporarily reserved by another checkout. No customer information is disclosed. Please try again shortly."
                    if request.LANGUAGE_CODE == "en"
                    else f"القطعة {labels} محجوزة مؤقتًا لعملية إتمام طلب أخرى. يمكنك المحاولة مجددًا بعد انتهاء الحجز."
                ),
            )
        if sold:
            labels = ", ".join(sold)
            messages.warning(
                request,
                (
                    f"{labels} is no longer available and was removed from checkout."
                    if request.LANGUAGE_CODE == "en"
                    else f"القطعة {labels} لم تعد متاحة وتمت إزالتها من مسار الشراء."
                ),
            )
        return redirect(ORDERS_CART_URL)
    bead_setting, _ = StoreSetting.objects.get_or_create(singleton=True)
    for bead_item in cart.items.select_related("product"):
        requested = bead_item.requested_bead_count
        original = bead_item.product.bead_count
        if requested is not None:
            if (
                not bead_setting.bead_adjustment_enabled
                or not original
                or original <= 33
                or requested < 33
                or requested >= original
            ):
                bead_item.requested_bead_count = None
                bead_item.save(update_fields=["requested_bead_count", "updated_at"])
                messages.warning(
                    request,
                    "تمت إزالة طلب ضبط خرز غير صالح بعد إعادة التحقق من بيانات القطعة."
                    if request.LANGUAGE_CODE != "en"
                    else "An invalid bead adjustment was removed after server validation.",
                )
                return redirect(ORDERS_CART_URL)
    ambassador_program = settings_obj()
    payment_policy = current_payment_policy()
    store_setting, _ = StoreSetting.objects.get_or_create(singleton=True)
    checkout_field_config = sanitise_checkout_field_config(
        store_setting.checkout_field_config
    )
    ambassador_balance = 0
    if (
        request.user.is_authenticated
        and getattr(request.user, "role", "") == "CUSTOMER"
    ):
        ambassador_balance = available_points(ensure_profile(request.user))
    if request.method == "GET":
        request.session["checkout_key"] = token_urlsafe(24)
        initial = {
            "idempotency_key": request.session["checkout_key"],
        }
        if request.user.is_authenticated:
            initial.update(
                {
                    "customer_name": request.user.get_full_name(),
                    "customer_email": request.user.email,
                    "customer_phone": request.user.phone_e164,
                    "country": request.user.country or "AE",
                }
            )
            saved = request.user.addresses.order_by(
                "-is_default", "-created_at"
            ).first()
            if saved:
                initial.update(
                    {
                        "country": saved.country,
                        "emirate": saved.emirate,
                        "city": saved.city,
                        "area": saved.area,
                        "street": saved.street,
                        "building": saved.building,
                        "apartment_or_villa": saved.apartment_or_villa,
                        "postal_code": saved.postal_code,
                        "additional_notes": saved.additional_notes,
                        "latitude": saved.latitude,
                        "longitude": saved.longitude,
                    }
                )
        form = CheckoutForm(
            initial=initial, checkout_field_config=checkout_field_config
        )
        _configure_ambassador_checkout_fields(form, request, ambassador_program)
    else:
        form = CheckoutForm(
            request.POST, checkout_field_config=checkout_field_config
        )
        _configure_ambassador_checkout_fields(form, request, ambassador_program)
        if form.is_valid():
            customer = form.cleaned_data.copy()
            key = customer.pop("idempotency_key", "")
            expected = request.session.get("checkout_key", "")
            if not expected or key != expected:
                messages.error(
                    request,
                    (
                        "انتهت جلسة إتمام الطلب، حاول مرة أخرى."
                        if request.LANGUAGE_CODE != "en"
                        else "Your checkout session expired. Please try again."
                    ),
                )
                return redirect("orders:checkout")
            try:
                order = create_order_from_cart(
                    cart=cart,
                    customer=customer,
                    user=request.user if request.user.is_authenticated else None,
                    idempotency_key=key,
                )
            except ValueError as exc:
                messages.error(request, _cart_error_message(exc, request.LANGUAGE_CODE))
                return redirect(ORDERS_CART_URL)
            request.session.pop("checkout_key", None)
            request.session["recent_order"] = str(order.public_id)
            audit(
                request,
                "checkout_order_created",
                order,
                new={
                    "reference": order.reference,
                    "currency": order.currency,
                    "grand_total": str(order.grand_total),
                    "status": order.status,
                    "payment_status": order.payment_status,
                    "item_count": order.items.count(),
                    "customer_mode": (
                        "authenticated" if request.user.is_authenticated else "guest"
                    ),
                },
            )
            if payment_policy.online and not payment_policy.manual:
                try:
                    session = create_checkout_session(order=order, request=request)
                    return redirect(session.url)
                except Exception:
                    # The order and inventory reservation remain valid; the customer can retry
                    # payment from the confirmation page. Never expose provider internals.
                    messages.error(
                        request,
                        (
                            "تعذر فتح بوابة الدفع الآن. طلبك محفوظ ويمكنك إعادة المحاولة."
                            if request.LANGUAGE_CODE != "en"
                            else "We could not open the payment page. Your order is saved and you can retry."
                        ),
                    )
            return redirect(ORDERS_CONFIRMATION_URL, public_id=order.public_id)
    return render(
        request,
        "orders/checkout.html",
        {
            "form": form,
            "cart": cart,
            "totals": totals(cart),
            "idempotency_key": request.session.get("checkout_key", ""),
            "saved_addresses": (
                request.user.addresses.order_by("-is_default", "-created_at")
                if request.user.is_authenticated
                else ()
            ),
            "ambassador_program": ambassador_program,
            "ambassador_balance": ambassador_balance,
            "payment_policy": payment_policy,
        },
    )


@require_GET
def confirmation(request, public_id):
    management_response = _management_order_redirect(request, public_id)
    if management_response is not None:
        return management_response
    order = Order.objects.prefetch_related("items").filter(public_id=public_id).first()
    if order is None or not _can_access_order(request, order):
        return _order_not_available(request)
    expire_unpaid_order_if_needed(order)
    order.refresh_from_db()
    payment_policy = current_payment_policy()
    deadline = reservation_deadline(order)
    reservation_active = bool(
        deadline
        and deadline > timezone.now()
        and order.payment_status != Order.PaymentStatus.PAID
        and order.status not in {Order.Status.CANCELLED, Order.Status.RETURNED}
    )
    return render(
        request,
        "orders/confirmation.html",
        {
            "order": order,
            "whatsapp_url": (
                whatsapp_url(order)
                if payment_policy.manual and reservation_active
                else ""
            ),
            "stripe_enabled": payment_policy.online and reservation_active,
            "manual_payment_enabled": payment_policy.manual and reservation_active,
            "payment_cancelled": request.GET.get("payment") == "cancelled",
            "reservation_deadline": deadline,
            "reservation_active": reservation_active,
        },
    )


@require_POST
def manual_payment_start(request, public_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"), public_id=public_id
    )
    if not _can_access_order(request, order):
        raise Http404
    expire_unpaid_order_if_needed(order)
    order.refresh_from_db()
    if order.status == Order.Status.CANCELLED:
        messages.error(
            request,
            (
                "انتهت مهلة حجز الطلب. أعد المحاولة من المتجر إذا كانت القطع ما زالت متاحة."
                if request.LANGUAGE_CODE != "en"
                else "The reservation expired. Start again from the store if the items are still available."
            ),
        )
        return redirect(ORDERS_CONFIRMATION_URL, public_id=order.public_id)
    if not current_payment_policy().manual:
        return HttpResponse(status=404)
    if order.payment_status == Order.PaymentStatus.PAID:
        return redirect(ORDERS_DETAIL_URL, public_id=order.public_id)
    if order.status in {Order.Status.CANCELLED, Order.Status.RETURNED}:
        return HttpResponse(status=409)
    destination = whatsapp_url(order)
    if not destination:
        messages.error(
            request,
            (
                "تعذر فتح واتساب لأن رقم التواصل غير مهيأ."
                if request.LANGUAGE_CODE != "en"
                else "WhatsApp cannot be opened because the store contact number is not configured."
            ),
        )
        return redirect(ORDERS_DETAIL_URL, public_id=order.public_id)

    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        locked_deadline = reservation_deadline(locked)
        if not locked_deadline or locked_deadline <= timezone.now():
            messages.error(
                request,
                (
                    "انتهت مهلة حجز الطلب. لا يمكن بدء التحويل اليدوي لهذا الطلب."
                    if request.LANGUAGE_CODE != "en"
                    else "The reservation expired. Manual payment cannot be started for this order."
                ),
            )
            return redirect(ORDERS_CONFIRMATION_URL, public_id=locked.public_id)
        active_stripe = (
            locked.payment_attempts.select_for_update()
            .filter(
                status__in=[
                    PaymentAttempt.Status.CREATING,
                    PaymentAttempt.Status.OPEN,
                    PaymentAttempt.Status.PROCESSING,
                ]
            )
            .exists()
        )
        if active_stripe:
            messages.warning(
                request,
                (
                    "لديك جلسة دفع إلكتروني نشطة. أكملها أو انتظر انتهاءها قبل التحويل اليدوي."
                    if request.LANGUAGE_CODE != "en"
                    else "An online payment session is still active. Complete it or wait for it to expire before switching to manual payment."
                ),
            )
            return redirect(ORDERS_DETAIL_URL, public_id=locked.public_id)
        if locked.payment_method != Order.PaymentMethod.MANUAL:
            old_method = locked.payment_method
            locked.payment_method = Order.PaymentMethod.MANUAL
            locked.save(update_fields=["payment_method", "updated_at"])
            OrderTimelineEvent.objects.create(
                order=locked,
                kind=OrderTimelineEvent.Kind.NOTE,
                label_ar="تم اختيار متابعة الدفع يدويًا عبر واتساب",
                label_en="Manual WhatsApp payment selected",
                from_value=old_method,
                to_value=Order.PaymentMethod.MANUAL,
            )
            audit(
                request,
                "manual_payment_selected",
                locked,
                {"payment_method": old_method},
                {"payment_method": Order.PaymentMethod.MANUAL},
            )
    return redirect(destination)


@require_POST
def stripe_payment_start(request, public_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"), public_id=public_id
    )
    if not _can_access_order(request, order):
        raise Http404
    expire_unpaid_order_if_needed(order)
    order.refresh_from_db()
    if order.status == Order.Status.CANCELLED:
        messages.error(
            request,
            (
                "انتهت مهلة حجز الطلب. لا يمكن بدء دفعة جديدة لهذا الطلب."
                if request.LANGUAGE_CODE != "en"
                else "The reservation expired. A new payment cannot be started for this order."
            ),
        )
        return redirect(ORDERS_CONFIRMATION_URL, public_id=order.public_id)
    if not current_payment_policy().online:
        return HttpResponse(status=404)
    try:
        session = create_checkout_session(order=order, request=request)
    except ValueError as exc:
        messages.error(
            request,
            (
                str(exc)
                if request.LANGUAGE_CODE == "en"
                else "تعذر بدء الدفع لهذا الطلب. يرجى التحقق من حالة الطلب والمحاولة مرة أخرى."
            ),
        )
        return redirect(ORDERS_CONFIRMATION_URL, public_id=order.public_id)
    except Exception:
        messages.error(
            request,
            (
                "تعذر الاتصال ببوابة الدفع. يرجى المحاولة مرة أخرى."
                if request.LANGUAGE_CODE != "en"
                else "Unable to connect to the payment provider. Please try again."
            ),
        )
        return redirect(ORDERS_CONFIRMATION_URL, public_id=order.public_id)
    return redirect(session.url)


@require_GET
def stripe_payment_success(request, public_id):
    management_response = _management_order_redirect(request, public_id)
    if management_response is not None:
        return management_response
    order = Order.objects.prefetch_related("items").filter(public_id=public_id).first()
    if order is None or not _can_access_order(request, order):
        return _order_not_available(request)
    # Webhooks remain authoritative. This server-to-server reconciliation is a
    # safe fallback when the browser returns before a webhook arrives or when a
    # delivery was temporarily missed. No browser-supplied payment state is trusted.
    reconciliation = "not_attempted"
    if settings.STRIPE_ENABLED and order.payment_status != Order.PaymentStatus.PAID:
        try:
            reconciliation = reconcile_order_payment(order)
        except Exception:
            reconciliation = "unavailable"
    order.refresh_from_db()
    return render(
        request,
        "orders/payment_success.html",
        {
            "order": order,
            "reconciliation": reconciliation,
        },
    )


@login_required
@require_GET
def my_orders(request):
    """Customer history; management identities stay on management surfaces."""
    if _is_management_user(request):
        if can(request.user, "view_orders"):
            return redirect("core:management_orders")
        return redirect("core:management_dashboard")

    _reconcile_customer_expired_orders(request.user)
    base_qs = Order.objects.filter(user=request.user)

    active_statuses = [
        Order.Status.PENDING,
        Order.Status.CONFIRMED,
        Order.Status.PREPARING,
        Order.Status.READY,
        Order.Status.SHIPPED,
        Order.Status.OUT_FOR_DELIVERY,
    ]
    completed_statuses = [
        Order.Status.DELIVERED,
        Order.Status.CANCELLED,
        Order.Status.RETURNED,
    ]

    summary = {
        "active": base_qs.filter(status__in=active_statuses).count(),
        "completed": base_qs.filter(status=Order.Status.DELIVERED).count(),
        "cancelled": base_qs.filter(
            status__in=[Order.Status.CANCELLED, Order.Status.RETURNED]
        ).count(),
        "total": base_qs.count(),
    }

    query = (request.GET.get("q") or "").strip()[:80]
    scope = request.GET.get("scope") or "active"
    if scope not in {"active", "completed", "all"}:
        scope = "active"

    status = request.GET.get("status") or ""
    allowed_statuses = {choice for choice, _label in Order.Status.choices}
    if status not in allowed_statuses:
        status = ""

    orders = base_qs
    if scope == "active":
        orders = orders.filter(status__in=active_statuses)
    elif scope == "completed":
        orders = orders.filter(status__in=completed_statuses)

    if status:
        orders = orders.filter(status=status)

    if query:
        orders = orders.filter(
            Q(reference__icontains=query)
            | Q(items__sku__icontains=query)
            | Q(items__product_reference__icontains=query)
            | Q(items__name_ar__icontains=query)
            | Q(items__name_en__icontains=query)
        ).distinct()

    orders = orders.order_by("-created_at")
    paginator = Paginator(orders, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    now = timezone.now()
    payment_policy = current_payment_policy()
    for order in page_obj.object_list:
        deadline = reservation_deadline(order)
        order.checkout_deadline = deadline
        order.checkout_active = bool(
            deadline
            and deadline > now
            and order.payment_status != Order.PaymentStatus.PAID
            and order.status
            not in {
                Order.Status.CANCELLED,
                Order.Status.RETURNED,
                Order.Status.DELIVERED,
            }
        )
        order.checkout_seconds_remaining = (
            max(0, int((deadline - now).total_seconds()))
            if order.checkout_active
            else 0
        )
        order.can_resume_payment = bool(
            order.checkout_active and (payment_policy.online or payment_policy.manual)
        )

    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        "orders/my_orders.html",
        {
            "page_obj": page_obj,
            "orders": page_obj.object_list,
            "summary": summary,
            "query": query,
            "scope": scope,
            "status_filter": status,
            "status_choices": Order.Status.choices,
            "querystring": query_params.urlencode(),
        },
    )


@login_required
@require_GET
def order_detail(request, public_id):
    management_response = _management_order_redirect(request, public_id)
    if management_response is not None:
        return management_response
    order = (
        Order.objects.prefetch_related("items", "timeline")
        .filter(public_id=public_id, user=request.user)
        .first()
    )
    if order is None:
        return _order_not_available(request)
    expire_unpaid_order_if_needed(order)
    order.refresh_from_db()
    payment_policy = current_payment_policy()
    deadline = reservation_deadline(order)
    reservation_active = bool(
        deadline
        and deadline > timezone.now()
        and order.status not in {Order.Status.CANCELLED, Order.Status.RETURNED}
    )
    item_list = list(order.items.all())
    primary_items = item_list[:8]
    additional_items = item_list[8:]
    delivery_rank = {
        Order.Status.CONFIRMED: 0,
        Order.Status.PREPARING: 1,
        Order.Status.READY: 2,
        Order.Status.SHIPPED: 3,
        Order.Status.OUT_FOR_DELIVERY: 4,
        Order.Status.DELIVERED: 5,
    }.get(order.status, -1)
    stripe_retry_allowed = (
        payment_policy.online
        and order.payment_status
        in {
            Order.PaymentStatus.UNPAID,
            Order.PaymentStatus.PENDING,
            Order.PaymentStatus.FAILED,
        }
        and order.status not in {Order.Status.CANCELLED, Order.Status.RETURNED}
        and reservation_active
    )
    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "stripe_retry_allowed": stripe_retry_allowed,
            "manual_payment_enabled": payment_policy.manual,
            "whatsapp_url": whatsapp_url(order) if payment_policy.manual else "",
            "primary_items": primary_items,
            "additional_items": additional_items,
            "item_count": len(item_list),
            "delivery_rank": delivery_rank,
            "reservation_deadline": deadline,
            "reservation_active": reservation_active,
        },
    )


def _tracking_status_context(order):
    """Return presentation-only tracking state derived from persisted order data.

    Keep this server-side so the browser cannot invent fulfillment progress.
    """
    ar_labels = {
        Order.Status.PENDING: "بانتظار التأكيد",
        Order.Status.CONFIRMED: "تم التأكيد",
        Order.Status.PREPARING: "جاري التجهيز",
        Order.Status.READY: "جاهز للتوصيل",
        Order.Status.SHIPPED: "تم الشحن",
        Order.Status.OUT_FOR_DELIVERY: "خرج للتوصيل",
        Order.Status.DELIVERED: "تم التسليم",
        Order.Status.CANCELLED: "تم الإلغاء",
        Order.Status.RETURNED: "مرتجع",
    }
    payment_ar = {
        Order.PaymentStatus.UNPAID: "غير مدفوع",
        Order.PaymentStatus.PENDING: "قيد الدفع",
        Order.PaymentStatus.PAID: "مدفوع",
        Order.PaymentStatus.FAILED: "تعذر الدفع",
        Order.PaymentStatus.REFUNDED: "مسترد",
        Order.PaymentStatus.PARTIAL: "مسترد جزئيًا",
    }
    flow = [
        (Order.Status.CONFIRMED, "تم التأكيد", "Confirmed"),
        (Order.Status.PREPARING, "جاري التجهيز", "Preparing"),
        (Order.Status.READY, "جاهز للتوصيل", "Ready for delivery"),
        (Order.Status.SHIPPED, "تم الشحن", "Shipped"),
        (Order.Status.OUT_FOR_DELIVERY, "خرج للتوصيل", "Out for delivery"),
        (Order.Status.DELIVERED, "تم التسليم", "Delivered"),
    ]
    rank = {value: idx for idx, (value, _ar, _en) in enumerate(flow)}
    current_rank = rank.get(order.status, -1)
    steps = [
        {
            "code": value,
            "label_ar": label_ar,
            "label_en": label_en,
            "complete": current_rank >= idx,
            "current": current_rank == idx,
        }
        for idx, (value, label_ar, label_en) in enumerate(flow)
    ]
    return {
        "status_label_ar": ar_labels.get(order.status, order.get_status_display()),
        "payment_label_ar": payment_ar.get(
            order.payment_status, order.get_payment_status_display()
        ),
        "tracking_steps": steps,
        "tracking_terminal_state": order.status
        in {Order.Status.CANCELLED, Order.Status.RETURNED},
    }


@require_http_methods(["GET", "POST"])
def track_order(request):
    # Public tracking deliberately requires two matching values.  Keep the
    # response generic on failure to avoid order-reference enumeration.
    form = OrderTrackingForm(request.POST or None)
    order = None
    attempted = request.method == "POST"
    context = {"form": form, "order": None, "attempted": attempted}
    if attempted and form.is_valid():
        order = (
            Order.objects.filter(
                reference=form.cleaned_data["reference"].upper(),
                customer_phone=form.cleaned_data["phone"],
            )
            .prefetch_related("items", "timeline")
            .first()
        )
        if order is not None:
            context["order"] = order
            context.update(_tracking_status_context(order))
    return render(request, "orders/track.html", context)

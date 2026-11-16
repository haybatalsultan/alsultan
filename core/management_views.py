import logging
import uuid
from decimal import Decimal
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Count, F, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.forms import SupervisorCreateForm
from accounts.models import SecurityEvent, SupervisorPermission, User
from accounts.services.mfa_service import mfa_enabled, session_mfa_verified
from accounts.services.permission_service import can, require_owner, require_permission
from ambassadors.models import Referral
from catalog.models import (
    Category,
    InventoryTransaction,
    Material,
    Product,
    ProductImage,
    Promotion,
    ProductCustodyHistory,
)
from catalog.services.image_service import (
    attach_product_images,
    delete_master_data_image,
    delete_product_image,
    set_primary_image,
    update_image_metadata,
    upload_master_data_image,
)
from catalog.services.promotion_service import attach_offer_snapshots
from core.forms import (
    CategoryManagementForm,
    ExpenseForm,
    ExpenseVoidForm,
    HandToHandDeliveryForm,
    InventoryAdjustmentForm,
    InvoiceIdentitySettingsForm,
    ManagementProductForm,
    ManualPaymentConfirmationForm,
    MaterialManagementForm,
    OrderStatusForm,
    PaymentStatusForm,
    PricingForm,
    ProductImageMetadataForm,
    ProductImageUploadForm,
    PromotionManagementForm,
    QuickSaleForm,
    QuickSaleProductSearchForm,
    DirectPaymentEntryForm,
    ProductCustodyForm,
    ReservationExtensionForm,
    ShippingDetailsForm,
    SupervisorPermissionForm,
)
from core.models import AuditLog, StoreSetting
from core.services.audit_service import audit, verify_integrity
from core.services.checkout_fields import (
    CONFIGURABLE_CHECKOUT_FIELDS,
    sanitise_checkout_field_config,
)
from orders.models import (
    Cart,
    Expense,
    Order,
    DirectPaymentEntry,
    Invoice,
    OrderTimelineEvent,
    PaymentAttempt,
    Reservation,
    ReservationLimitOverride,
    ReservationLimitRequest,
)
from orders.services.accountant_service import build_accountant_report
from orders.services.invoice_service import create_invoice_snapshot, render_invoice_pdf
from orders.services.inventory_service import (
    consume_order_reservations,
    release_order_reservations,
)
from orders.services.loyalty_service import (
    annotate_customer_loyalty,
    loyalty_label_from_count,
)
from orders.services.risk_service import customer_risk_signals
from orders.services.quick_sale_service import QuickSaleError, create_quick_sale
from orders.services.stripe_service import reconcile_order_payment

MANAGEMENT_PAYMENT_SETTINGS_URL = 'core:management_payment_settings'
MANAGEMENT_EXPENSES_URL = 'core:management_expenses'
MANAGEMENT_CATEGORIES_URL = 'core:management_categories'
MANAGEMENT_FORM_TEMPLATE = 'management/form.html'
MANAGEMENT_MATERIALS_URL = 'core:management_materials'
MANAGEMENT_PRODUCTS_URL = 'core:management_products'
MANAGEMENT_PRODUCT_IMAGES_URL = 'core:management_product_images'
MANAGEMENT_ORDER_URL = 'core:management_order'
MANAGEMENT_PROMOTIONS_URL = 'core:management_promotions'
MANAGEMENT_RESERVATION_OVERRIDES_URL = 'core:management_reservation_overrides'

logger = logging.getLogger("haybat.security")


def staff_required(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.user.role not in {User.Role.OWNER, User.Role.SUPERVISOR}:
            raise PermissionDenied
        if not mfa_enabled(request.user):
            return redirect("accounts:mfa_setup")
        if not session_mfa_verified(request, request.user):
            from django.contrib.auth import logout

            logout(request)
            return redirect("accounts:login")
        return view(request, *args, **kwargs)

    return wrapped


def _clean_search(request, max_length=100):
    return (request.GET.get("q") or "").strip()[:max_length]


def _last_public_item_code():
    """Return the last persisted HS item code for management display only.

    This value is informational. It is never used to allocate or predict the
    next SKU; Product.save() remains the only authority for SKU generation.
    """
    return (
        Product.objects.exclude(sku__isnull=True)
        .exclude(sku="")
        .order_by("-pk")
        .values_list("sku", flat=True)
        .first()
    )


def _paginate(request, queryset, per_page=25):
    paginator = Paginator(queryset, per_page, orphans=2)
    page_obj = paginator.get_page(request.GET.get("page"))
    page_obj.display_range = paginator.get_elided_page_range(
        page_obj.number, on_each_side=2, on_ends=1
    )
    params = request.GET.copy()
    params.pop("page", None)
    return page_obj, params.urlencode()


def page_copy(request, ar_title, en_title, ar_description="", en_description=""):
    is_en = request.LANGUAGE_CODE == "en"
    return {
        "page_title": en_title if is_en else ar_title,
        "page_description": en_description if is_en else ar_description,
    }


@staff_required
def payment_settings(request):
    require_owner(request.user)
    store, _ = StoreSetting.objects.get_or_create(
        singleton=True,
        defaults={
            "online_payment_enabled": bool(settings.STRIPE_ENABLED),
            "whatsapp_checkout_enabled": True,
        },
    )
    if request.method == "POST":
        online = request.POST.get("online_payment_enabled") == "on"
        manual = request.POST.get("whatsapp_checkout_enabled") == "on"
        if not online and not manual:
            messages.error(
                request,
                "يجب تفعيل طريقة دفع واحدة على الأقل."
                if request.LANGUAGE_CODE != "en"
                else "At least one payment method must remain enabled.",
            )
            return redirect(MANAGEMENT_PAYMENT_SETTINGS_URL)
        if online and not settings.STRIPE_ENABLED:
            messages.error(
                request,
                "لا يمكن تفعيل الدفع الإلكتروني قبل اكتمال إعداد Stripe الآمن."
                if request.LANGUAGE_CODE != "en"
                else "Online payment cannot be enabled until Stripe is securely configured.",
            )
            return redirect(MANAGEMENT_PAYMENT_SETTINGS_URL)
        with transaction.atomic():
            locked = StoreSetting.objects.select_for_update().get(pk=store.pk)
            old = {
                "online_payment_enabled": locked.online_payment_enabled,
                "whatsapp_checkout_enabled": locked.whatsapp_checkout_enabled,
            }
            locked.online_payment_enabled = online
            locked.whatsapp_checkout_enabled = manual
            locked.save(
                update_fields=[
                    "online_payment_enabled",
                    "whatsapp_checkout_enabled",
                    "updated_at",
                ]
            )
            audit(
                request,
                "payment_methods_updated",
                locked,
                old,
                {
                    "online_payment_enabled": online,
                    "whatsapp_checkout_enabled": manual,
                },
            )
        messages.success(
            request,
            "تم تحديث طرق الدفع بنجاح."
            if request.LANGUAGE_CODE != "en"
            else "Payment methods updated successfully.",
        )
        return redirect(MANAGEMENT_PAYMENT_SETTINGS_URL)
    return render(
        request,
        "management/payment_settings.html",
        {
            "store_setting": store,
            "stripe_configured": bool(settings.STRIPE_ENABLED),
            **page_copy(
                request,
                "طرق الدفع",
                "Payment Methods",
                "تحكم المالك بطرق الدفع المتاحة للعملاء دون تغيير الكود.",
                "Owner-controlled customer payment methods without code changes.",
            ),
        },
    )



@staff_required
def bead_adjustment_settings(request):
    require_owner(request.user)
    store, _ = StoreSetting.objects.get_or_create(singleton=True)
    if request.method == "POST":
        enabled = request.POST.get("bead_adjustment_enabled") == "on"
        with transaction.atomic():
            locked = StoreSetting.objects.select_for_update().get(pk=store.pk)
            old = locked.bead_adjustment_enabled
            locked.bead_adjustment_enabled = enabled
            locked.save(update_fields=["bead_adjustment_enabled", "updated_at"])
            audit(
                request,
                "bead_adjustment_settings_updated",
                locked,
                old={"bead_adjustment_enabled": old},
                new={"bead_adjustment_enabled": enabled},
            )
        messages.success(request, "تم تحديث خدمة ضبط عدد الخرز.")
        return redirect("core:management_bead_adjustment_settings")
    return render(
        request,
        "management/bead_adjustment_settings.html",
        {"store_setting": store, **page_copy(request, "خدمة ضبط الخرز", "Bead Adjustment Service")},
    )

@staff_required
def checkout_field_settings(request):
    """Owner-only configuration for safe, persistence-compatible checkout fields."""
    require_owner(request.user)
    store, _ = StoreSetting.objects.get_or_create(singleton=True)
    current = sanitise_checkout_field_config(store.checkout_field_config)

    if request.method == "POST":
        submitted = {}
        for name in CONFIGURABLE_CHECKOUT_FIELDS:
            visible = request.POST.get(f"{name}_visible") == "on"
            required = visible and request.POST.get(f"{name}_required") == "on"
            submitted[name] = {"visible": visible, "required": required}
        submitted = sanitise_checkout_field_config(submitted)

        with transaction.atomic():
            locked = StoreSetting.objects.select_for_update().get(pk=store.pk)
            old = sanitise_checkout_field_config(locked.checkout_field_config)
            locked.checkout_field_config = submitted
            locked.save(update_fields=["checkout_field_config", "updated_at"])
            audit(
                request,
                "checkout_field_settings_updated",
                locked,
                old={"checkout_field_config": old},
                new={"checkout_field_config": submitted},
            )

        messages.success(
            request,
            "تم تحديث إعدادات حقول إتمام الطلب بنجاح."
            if request.LANGUAGE_CODE != "en"
            else "Checkout field settings updated successfully.",
        )
        return redirect("core:management_checkout_field_settings")

    labels_ar = {
        "customer_email": "البريد الإلكتروني",
        "emirate": "الإمارة / المنطقة",
        "city": "المدينة",
        "street": "الشارع",
        "building": "المبنى",
        "apartment_or_villa": "الشقة / الفيلا",
        "postal_code": "الرمز البريدي",
        "additional_notes": "ملاحظات التوصيل",
    }
    labels_en = {
        "customer_email": "Email",
        "emirate": "Emirate / Region",
        "city": "City",
        "street": "Street",
        "building": "Building",
        "apartment_or_villa": "Apartment / Villa",
        "postal_code": "Postal code",
        "additional_notes": "Delivery notes",
    }
    labels = labels_en if request.LANGUAGE_CODE == "en" else labels_ar
    rows = [
        {
            "name": name,
            "label": labels[name],
            "visible": current[name]["visible"],
            "required": current[name]["required"],
        }
        for name in CONFIGURABLE_CHECKOUT_FIELDS
    ]
    protected = (
        ["Full name", "Mobile number", "Country", "Area / District", "Terms & Returns acceptance"]
        if request.LANGUAGE_CODE == "en"
        else ["الاسم الكامل", "رقم الهاتف", "الدولة", "المنطقة / الحي", "الموافقة على الشروط وسياسة الاسترجاع"]
    )
    return render(
        request,
        "management/checkout_field_settings.html",
        {
            "field_rows": rows,
            "protected_fields": protected,
            **page_copy(
                request,
                "حقول إتمام الطلب",
                "Checkout Fields",
                "حدد الحقول الظاهرة والإجبارية للعملاء. الحقول الحساسة للنظام محمية ولا يمكن تعطيلها.",
                "Choose which customer fields are visible or required. System-critical fields are protected.",
            ),
        },
    )


@staff_required
def notification_settings(request):
    require_owner(request.user)
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email

    store, _ = StoreSetting.objects.get_or_create(singleton=True)
    if request.method == "POST":
        email = (request.POST.get("notification_email") or "").strip()[:254]
        if email:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(
                    request,
                    "أدخل بريدًا إلكترونيًا صحيحًا."
                    if request.LANGUAGE_CODE != "en"
                    else "Enter a valid email address.",
                )
                return redirect("core:management_notification_settings")
        values = {
            "notification_email": email,
            "notify_admin_new_order": request.POST.get("notify_admin_new_order")
            == "on",
            "notify_admin_payment": request.POST.get("notify_admin_payment") == "on",
            "notify_admin_shipping": request.POST.get("notify_admin_shipping") == "on",
            "notify_customer_payment": request.POST.get("notify_customer_payment")
            == "on",
            "notify_customer_shipping": request.POST.get("notify_customer_shipping")
            == "on",
        }
        with transaction.atomic():
            locked = StoreSetting.objects.select_for_update().get(pk=store.pk)
            old = {k: getattr(locked, k) for k in values}
            for key, value in values.items():
                setattr(locked, key, value)
            locked.save(update_fields=[*values.keys(), "updated_at"])
            audit(request, "notification_settings_updated", locked, old, values)
        messages.success(
            request,
            "تم تحديث إعدادات التنبيهات."
            if request.LANGUAGE_CODE != "en"
            else "Notification settings updated.",
        )
        return redirect("core:management_notification_settings")
    return render(
        request,
        "management/notification_settings.html",
        {
            "store_setting": store,
            "fallback_email": settings.STORE_CONTACT_EMAIL,
            **page_copy(
                request,
                "تنبيهات الطلبات",
                "Order Notifications",
                "إدارة تنبيهات الطلب والدفع والشحن بدون كشف بيانات حساسة.",
                "Manage order, payment and shipping notifications without exposing sensitive data.",
            ),
        },
    )


@staff_required
def dashboard(request):
    active_products = Product.objects.exclude(status=Product.Status.ARCHIVED).annotate(
        free_quantity=F("available_quantity") - F("reserved_quantity")
    )
    is_owner = request.user.role == User.Role.OWNER
    can_orders = can(request.user, "view_orders")
    can_products = can(request.user, "view_products")
    order_qs = Order.objects.all() if can_orders else Order.objects.none()

    ctx = {
        "orders": order_qs.count(),
        "awaiting_payment": order_qs.filter(
            payment_status__in=[Order.PaymentStatus.UNPAID, Order.PaymentStatus.PENDING]
        )
        .exclude(status__in=[Order.Status.CANCELLED, Order.Status.RETURNED])
        .count(),
        "paid_confirmed": order_qs.filter(
            payment_status=Order.PaymentStatus.PAID,
            status=Order.Status.CONFIRMED,
        ).count(),
        "preparing": order_qs.filter(status=Order.Status.PREPARING).count(),
        "ready_delivery": order_qs.filter(status=Order.Status.READY).count(),
        "out_for_delivery": order_qs.filter(
            status=Order.Status.OUT_FOR_DELIVERY
        ).count(),
        "delivered": order_qs.filter(status=Order.Status.DELIVERED).count(),
        "products": active_products.count() if can_products else 0,
        "available_products": active_products.filter(free_quantity__gt=0).count()
        if can_products
        else 0,
        "sold_out_products": active_products.filter(free_quantity__lte=0).count()
        if can_products
        else 0,
        "low_stock": active_products.filter(
            free_quantity__gt=0, free_quantity__lte=1
        ).count()
        if can_products
        else 0,
        "recent_orders": (
            Order.objects.only(
                "public_id",
                "reference",
                "customer_name",
                "grand_total",
                "status",
                "payment_status",
                "payment_method",
                "created_at",
            ).order_by("-created_at")[:8]
            if can_orders
            else []
        ),
        "can_view_products": can_products,
        "can_view_orders": can_orders,
        "can_manage_delivery": can(request.user, "prepare_orders")
        or can(request.user, "ship_orders"),
        "can_view_customers": can(request.user, "view_customers"),
        "can_view_ambassadors": is_owner or can(request.user, "view_customers"),
        "is_owner": is_owner,
        "can_manage_master_data": can(request.user, "manage_master_data"),
        "can_view_abandoned_carts": can(request.user, "view_abandoned_carts"),
        "active_promotions": Promotion.objects.filter(
            is_active=True, starts_at__lte=timezone.now(), ends_at__gt=timezone.now()
        ).count()
        if is_owner
        else 0,
    }
    if is_owner:
        paid_orders = Order.objects.filter(payment_status=Order.PaymentStatus.PAID)
        ctx["revenue"] = paid_orders.aggregate(v=Sum("grand_total"))["v"] or 0
        ctx["refunded_total"] = (
            Order.objects.filter(
                payment_status__in=[
                    Order.PaymentStatus.REFUNDED,
                    Order.PaymentStatus.PARTIAL,
                ]
            ).aggregate(v=Sum("grand_total"))["v"]
            or 0
        )
        today = timezone.localdate()
        ctx["today_revenue"] = (
            paid_orders.filter(
                Q(payment_attempts__paid_at__date=today) | Q(manual_paid_at__date=today)
            )
            .distinct()
            .aggregate(v=Sum("grand_total"))["v"]
            or 0
        )
        ctx["pending_reservation_requests"] = ReservationLimitRequest.objects.filter(
            status=ReservationLimitRequest.Status.PENDING
        ).count()
        today = timezone.localdate()
        ctx["receivables_alert_count"] = Order.objects.filter(
            sale_channel=Order.SaleChannel.DIRECT,
            payment_status__in=[Order.PaymentStatus.UNPAID, Order.PaymentStatus.PARTIALLY_PAID],
            payment_due_date__isnull=False,
            payment_due_date__lte=today + timedelta(days=3),
        ).count()
    return render(request, "management/dashboard.html", ctx)


@staff_required
@require_GET
def quick_sale_product_search(request):
    require_owner(request.user)

    form = QuickSaleProductSearchForm(request.GET)
    if not form.is_valid():
        return JsonResponse({"results": []}, status=400)

    q = form.cleaned_data["q"]
    products = (
        Product.objects.filter(
            status=Product.Status.AVAILABLE,
            available_quantity__gt=F("reserved_quantity"),
        )
        .select_related("category", "material")
        .prefetch_related("images")
    )

    if q:
        products = products.filter(
            Q(sku__iexact=q)
            | Q(product_reference__iexact=q)
            | Q(sku__icontains=q)
            | Q(product_reference__icontains=q)
            | Q(name_ar__icontains=q)
            | Q(name_en__icontains=q)
            | Q(material__name_ar__icontains=q)
            | Q(material__name_en__icontains=q)
        )

    # Exact item-code hits naturally rank first, then stable SKU order.
    products = list(products.order_by("sku")[:10])
    attach_offer_snapshots(products)

    results = []
    for product in products:
        primary = next((image for image in product.images.all() if image.is_primary), None)
        if primary is None:
            primary = next(iter(product.images.all()), None)
        offer = product.offer_snapshot
        results.append({
            "id": product.pk,
            "sku": product.sku or "",
            "reference": product.product_reference,
            "name_ar": product.name_ar,
            "name_en": product.name_en,
            "material_ar": product.material.name_ar if product.material_id else "",
            "material_en": product.material.name_en if product.material_id else "",
            "bead_count": product.bead_count,
            "bead_size_mm": str(product.bead_size_mm) if product.bead_size_mm is not None else "",
            "weight_g": str(product.weight_g) if product.weight_g is not None else "",
            "verification_status": product.verification_status,
            "price": str(offer["final_price"]),
            "base_price": str(offer["base_price"]),
            "has_discount": bool(offer["has_discount"]),
            "image_url": primary.secure_url if primary else "",
        })

    return JsonResponse({"results": results})


@staff_required
def quick_sale(request):
    require_owner(request.user)
    initial = {"idempotency_key": str(uuid.uuid4())}
    form = QuickSaleForm(request.POST or None, initial=initial)

    if request.method == "POST" and form.is_valid():
        try:
            order, created = create_quick_sale(
                owner=request.user,
                cleaned_data=form.cleaned_data,
            )
        except QuickSaleError as exc:
            form.add_error(None, str(exc))
        else:
            if created:
                item = order.items.first()
                audit(
                    request,
                    "order_quick_sale_created",
                    order,
                    new={
                        "reference": order.reference,
                        "sale_channel": order.sale_channel,
                        "payment_status": order.payment_status,
                        "payment_method": order.payment_method,
                        "grand_total": order.grand_total,
                        "sku": item.sku if item else "",
                    },
                    metadata={"direct_sale": True},
                )
            return redirect("core:management_quick_sale_success", public_id=order.public_id)

    return render(request, "management/quick_sale.html", {
        "form": form,
        **page_copy(
            request,
            "بيع مباشر",
            "Quick Sale",
            "تسجيل بيع مباشر آمن لقطعة متوفرة. السعر والمخزون يعاد التحقق منهما من السيرفر عند التأكيد.",
            "Securely record an in-person sale. Price and stock are revalidated server-side on confirmation.",
        ),
    })


@staff_required
def quick_sale_success(request, public_id):
    require_owner(request.user)
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        public_id=public_id,
        sale_channel=Order.SaleChannel.DIRECT,
    )
    return render(request, "management/quick_sale_success.html", {
        "order": order,
        "item": order.items.first(),
        **page_copy(request, "تم البيع المباشر", "Direct Sale Completed"),
    })


@staff_required
def smart_accountant(request):
    require_owner(request.user)

    report = build_accountant_report(request)
    risk_signals = customer_risk_signals(days=30, limit=40)

    insights = []
    if report["legacy_delivered_without_timestamp"]:
        insights.append(
            {
                "level": "warning",
                "ar": f"يوجد {report['legacy_delivered_without_timestamp']} طلبًا مسلّمًا قديمًا بدون تاريخ تسليم مستقل؛ لا يتم وضعه في فترة مالية تخمينية.",
                "en": f"{report['legacy_delivered_without_timestamp']} legacy delivered order(s) have no dedicated delivery timestamp; they are not assigned to a guessed financial period.",
            }
        )
    if report["missing_cost_items"]:
        insights.append(
            {
                "level": "warning",
                "ar": f"يوجد {report['missing_cost_items']} بند طلب قديم بدون Snapshot تاريخي للتكلفة؛ لم يتم اختلاق تكلفة له.",
                "en": f"{report['missing_cost_items']} legacy order item(s) have no historical cost snapshot; no cost was fabricated.",
            }
        )
    if report["product_sales"] > 0 and report["margin"] < 20:
        insights.append(
            {
                "level": "warning",
                "ar": "هامش الربح المحقق للفترة أقل من 20% ويستحق مراجعة الأسعار والخصومات.",
                "en": "Realized margin for the period is below 20%; review pricing and discounts.",
            }
        )
    if report["outstanding"] > report["sales"] and report["outstanding"] > 0:
        insights.append(
            {
                "level": "warning",
                "ar": "المبالغ غير المسددة للفترة أعلى من المبيعات المحققة.",
                "en": "Outstanding order value is higher than realized paid sales for the period.",
            }
        )
    if not insights:
        insights.append(
            {
                "level": "ok",
                "ar": "لا توجد ملاحظة مالية تلقائية حرجة ضمن القواعد الحالية لهذه الفترة.",
                "en": "No critical rule-based financial observation was detected for this period.",
            }
        )

    recent_expenses = (
        Expense.objects.filter(status=Expense.Status.ACTIVE)
        .select_related("order")
        .order_by("-incurred_on", "-created_at")[:8]
    )
    return render(
        request,
        "management/smart_accountant.html",
        {
            **report,
            "recent_expenses": recent_expenses,
            "risk_signals": risk_signals,
            "risk_count": len(risk_signals),
            "insights": insights,
            **page_copy(
                request,
                "المحاسب الذكي",
                "Smart Accountant",
                "لوحة مالية خاصة بالمالك تعتمد على بيانات السيرفر وSnapshots تاريخية للتكلفة.",
                "Owner-only financial dashboard based on server data and historical cost snapshots.",
            ),
        },
    )


@staff_required
def expenses(request):
    require_owner(request.user)
    category = (request.GET.get("category") or "").strip()[:32]
    allowed_categories = {value for value, _ in Expense.Category.choices}
    if category not in allowed_categories:
        category = ""
    queryset = Expense.objects.select_related(
        "order", "created_by", "updated_by", "voided_by"
    ).order_by("-incurred_on", "-created_at")
    if category:
        queryset = queryset.filter(category=category)
    page_obj, pagination_query = _paginate(request, queryset, per_page=25)
    from orders.services.expense_labels import category_choices

    return render(
        request,
        "management/expenses.html",
        {
            "page_obj": page_obj,
            "pagination_query": pagination_query,
            "selected_category": category,
            "expense_categories": category_choices(request.LANGUAGE_CODE),
            **page_copy(
                request,
                "المصروفات",
                "Expenses",
                "تسجيل ومراجعة مصروفات التشغيل الخاصة بالمالك.",
                "Owner-only operating expense register.",
            ),
        },
    )


@staff_required
def expense_create(request):
    require_owner(request.user)
    form = ExpenseForm(request.POST or None, language_code=request.LANGUAGE_CODE)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.updated_by = request.user
        obj.save()
        audit(
            request,
            "expense_created",
            obj,
            new={
                "category": obj.category,
                "description": obj.description,
                "amount": str(obj.amount),
                "incurred_on": obj.incurred_on.isoformat(),
                "supplier": obj.supplier,
                "invoice_reference": obj.invoice_reference,
                "order": obj.order.reference if obj.order_id else "",
            },
        )
        messages.success(
            request,
            "تم تسجيل المصروف بنجاح."
            if request.LANGUAGE_CODE != "en"
            else "Expense recorded successfully.",
        )
        return redirect(MANAGEMENT_EXPENSES_URL)
    return render(
        request,
        "management/expense_form.html",
        {
            "form": form,
            "editing": False,
            **page_copy(
                request,
                "إضافة مصروف",
                "Add Expense",
                "سجّل المصروف الفعلي بدون إضافته إلى تكلفة المنتج.",
                "Record an actual operating expense without changing product cost.",
            ),
        },
    )


@staff_required
def expense_edit(request, public_id):
    require_owner(request.user)
    obj = get_object_or_404(Expense, public_id=public_id)
    if obj.status == Expense.Status.VOIDED:
        raise PermissionDenied("Voided expenses are immutable.")
    old = {
        "category": obj.category,
        "description": obj.description,
        "amount": str(obj.amount),
        "incurred_on": obj.incurred_on.isoformat(),
        "supplier": obj.supplier,
        "invoice_reference": obj.invoice_reference,
        "order": obj.order.reference if obj.order_id else "",
    }
    form = ExpenseForm(
        request.POST or None, instance=obj, language_code=request.LANGUAGE_CODE
    )
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.updated_by = request.user
        updated.save()
        audit(
            request,
            "expense_updated",
            updated,
            old=old,
            new={
                "category": updated.category,
                "description": updated.description,
                "amount": str(updated.amount),
                "incurred_on": updated.incurred_on.isoformat(),
                "supplier": updated.supplier,
                "invoice_reference": updated.invoice_reference,
                "order": updated.order.reference if updated.order_id else "",
            },
        )
        messages.success(
            request,
            "تم تحديث المصروف."
            if request.LANGUAGE_CODE != "en"
            else "Expense updated.",
        )
        return redirect(MANAGEMENT_EXPENSES_URL)
    return render(
        request,
        "management/expense_form.html",
        {
            "form": form,
            "editing": True,
            "expense": obj,
            **page_copy(
                request,
                "تعديل المصروف",
                "Edit Expense",
                "تعديل سجل مصروف نشط مع حفظ أثر التدقيق.",
                "Edit an active expense while preserving the audit trail.",
            ),
        },
    )


@staff_required
def expense_void(request, public_id):
    require_owner(request.user)
    obj = get_object_or_404(Expense, public_id=public_id)
    if obj.status == Expense.Status.VOIDED:
        messages.info(
            request,
            "المصروف ملغى بالفعل."
            if request.LANGUAGE_CODE != "en"
            else "Expense is already voided.",
        )
        return redirect(MANAGEMENT_EXPENSES_URL)
    form = ExpenseVoidForm(request.POST or None, language_code=request.LANGUAGE_CODE)
    if request.method == "POST" and form.is_valid():
        old = {"status": obj.status, "amount": str(obj.amount), "void_reason": ""}
        obj.status = Expense.Status.VOIDED
        obj.void_reason = form.cleaned_data["reason"]
        obj.voided_by = request.user
        obj.voided_at = timezone.now()
        obj.updated_by = request.user
        obj.save()
        audit(
            request,
            "expense_voided",
            obj,
            old=old,
            new={
                "status": obj.status,
                "amount": str(obj.amount),
                "void_reason": obj.void_reason,
            },
        )
        messages.success(
            request,
            "تم إلغاء المصروف مع الاحتفاظ بسجل التدقيق."
            if request.LANGUAGE_CODE != "en"
            else "Expense voided; audit history preserved.",
        )
        return redirect(MANAGEMENT_EXPENSES_URL)
    return render(
        request,
        "management/expense_void.html",
        {
            "form": form,
            "expense": obj,
            **page_copy(
                request,
                "إلغاء المصروف",
                "Void Expense",
                "الإلغاء لا يحذف السجل المالي؛ يبقى محفوظًا للتدقيق.",
                "Voiding never deletes the financial record; it remains auditable.",
            ),
        },
    )


@staff_required
def master_data(request):
    require_permission(request.user, "manage_master_data")
    return render(
        request,
        "management/master_data.html",
        {
            "category_count": Category.objects.count(),
            "active_category_count": Category.objects.filter(is_active=True).count(),
            "material_count": Material.objects.count(),
            "active_material_count": Material.objects.filter(is_active=True).count(),
            **page_copy(
                request,
                "البيانات الرئيسية",
                "Master Data",
                "إدارة التصنيفات والخامات التي تظهر في نماذج المنتجات. متاحة للمالك والمشرف.",
                "Manage the categories and materials used by product forms. Available to owners and supervisors.",
            ),
        },
    )


@staff_required
def categories(request):
    require_permission(request.user, "manage_master_data")
    q = _clean_search(request)
    queryset = Category.objects.annotate(product_count=Count("products")).order_by(
        "sort_order", "name_en", "id"
    )
    if q:
        queryset = queryset.filter(
            Q(name_ar__icontains=q) | Q(name_en__icontains=q) | Q(slug__icontains=q)
        )
    page_obj, pagination_query = _paginate(request, queryset, 25)
    return render(
        request,
        "management/master_list.html",
        {
            "items": page_obj.object_list,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
            "q": q,
            "result_count": page_obj.paginator.count,
            "kind": "category",
            **page_copy(
                request,
                "التصنيفات",
                "Categories",
                "إضافة وتعديل وترتيب وأرشفة التصنيفات بدون حذف السجلات المرتبطة بالمنتجات.",
                "Create, edit, order and archive categories without deleting product-linked records.",
            ),
        },
    )


def _save_master_data_form(form, *, kind):
    """
    Persist Category/Material changes while keeping Cloudinary folder/public IDs
    server-controlled. A failed upload never writes a broken image URL to the DB.
    """
    obj = form.save(commit=False)
    upload = form.cleaned_data.get("image")
    remove_image = bool(form.cleaned_data.get("remove_image"))
    old_public_id = getattr(obj, "image_public_id", "") or ""

    uploaded_public_id = ""
    if upload:
        result, _metadata = upload_master_data_image(
            upload,
            kind=kind,
            public_id=obj.public_id,
        )
        uploaded_public_id = result["public_id"]
        obj.image_public_id = uploaded_public_id
        obj.image_url = result["secure_url"]
    elif remove_image:
        obj.image_public_id = ""
        obj.image_url = ""

    try:
        with transaction.atomic():
            obj.save()
            form.save_m2m()
    except Exception:
        if uploaded_public_id:
            try:
                delete_master_data_image(uploaded_public_id)
            except Exception as cleanup_exc:
                logger.warning(
                    "master_data_upload_cleanup_failed exception_type=%s",
                    type(cleanup_exc).__name__,
                )
        raise

    # Delete the previous Cloudinary asset only after the DB commit succeeds.
    # If Cloudinary cleanup fails, the application remains consistent and the
    # stale remote asset can be cleaned up later without breaking the record.
    if old_public_id and old_public_id != obj.image_public_id:
        try:
            delete_master_data_image(old_public_id)
        except Exception as cleanup_exc:
            logger.warning(
                "master_data_old_asset_cleanup_failed exception_type=%s",
                type(cleanup_exc).__name__,
            )

    return obj


@staff_required
def category_create(request):
    require_permission(request.user, "manage_master_data")
    form = CategoryManagementForm(
        request.POST or None,
        request.FILES or None,
        language_code=request.LANGUAGE_CODE,
    )
    if request.method == "POST" and form.is_valid():
        try:
            obj = _save_master_data_form(form, kind="categories")
        except Exception:
            form.add_error(
                "image",
                "تعذر رفع الصورة إلى Cloudinary. حاول مرة أخرى."
                if request.LANGUAGE_CODE != "en"
                else "Unable to upload the image to Cloudinary. Please try again.",
            )
        else:
            audit(
                request,
                "category_created",
                obj,
                new={
                    "name_ar": obj.name_ar,
                    "name_en": obj.name_en,
                    "is_active": obj.is_active,
                    "has_image": bool(obj.image_public_id),
                },
            )
            return redirect(MANAGEMENT_CATEGORIES_URL)
    return render(
        request,
        MANAGEMENT_FORM_TEMPLATE,
        {
            "form": form,
            "title": "Create Category"
            if request.LANGUAGE_CODE == "en"
            else "إضافة تصنيف",
            "page_description": "The URL slug and Cloudinary path are generated by the server."
            if request.LANGUAGE_CODE == "en"
            else "يُنشئ النظام الرابط الداخلي ومسار Cloudinary تلقائيًا.",
            "cancel_url_name": MANAGEMENT_CATEGORIES_URL,
            "current_image_url": "",
        },
    )


@staff_required
def category_edit(request, public_id):
    require_permission(request.user, "manage_master_data")
    obj = get_object_or_404(Category, public_id=public_id)
    form = CategoryManagementForm(
        request.POST or None,
        request.FILES or None,
        instance=obj,
        language_code=request.LANGUAGE_CODE,
    )
    if request.method == "POST" and form.is_valid():
        old = {
            "name_ar": obj.name_ar,
            "name_en": obj.name_en,
            "is_active": obj.is_active,
            "sort_order": obj.sort_order,
            "has_image": bool(obj.image_public_id),
        }
        try:
            updated = _save_master_data_form(form, kind="categories")
        except Exception:
            form.add_error(
                "image",
                "تعذر تحديث الصورة في Cloudinary. حاول مرة أخرى."
                if request.LANGUAGE_CODE != "en"
                else "Unable to update the Cloudinary image. Please try again.",
            )
        else:
            audit(
                request,
                "category_updated",
                updated,
                old=old,
                new={
                    "name_ar": updated.name_ar,
                    "name_en": updated.name_en,
                    "is_active": updated.is_active,
                    "sort_order": updated.sort_order,
                    "has_image": bool(updated.image_public_id),
                },
            )
            return redirect(MANAGEMENT_CATEGORIES_URL)
    return render(
        request,
        MANAGEMENT_FORM_TEMPLATE,
        {
            "form": form,
            "title": "Edit Category"
            if request.LANGUAGE_CODE == "en"
            else "تعديل التصنيف",
            "page_description": obj.slug,
            "cancel_url_name": MANAGEMENT_CATEGORIES_URL,
            "current_image_url": obj.image_url,
        },
    )


@staff_required
@require_POST
def category_toggle(request, public_id):
    require_permission(request.user, "manage_master_data")
    obj = get_object_or_404(Category, public_id=public_id)
    old = obj.is_active
    with transaction.atomic():
        obj.is_active = not obj.is_active
        obj.save(update_fields=["is_active"])
        audit(
            request,
            "category_status_changed",
            obj,
            old={"is_active": old},
            new={"is_active": obj.is_active},
        )
    return redirect(MANAGEMENT_CATEGORIES_URL)


@staff_required
def materials(request):
    require_permission(request.user, "manage_master_data")
    q = _clean_search(request)
    queryset = Material.objects.annotate(product_count=Count("products")).order_by(
        "sort_order", "name_en", "id"
    )
    if q:
        queryset = queryset.filter(
            Q(name_ar__icontains=q) | Q(name_en__icontains=q) | Q(slug__icontains=q)
        )
    page_obj, pagination_query = _paginate(request, queryset, 25)
    return render(
        request,
        "management/master_list.html",
        {
            "items": page_obj.object_list,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
            "q": q,
            "result_count": page_obj.paginator.count,
            "kind": "material",
            **page_copy(
                request,
                "الخامات",
                "Materials",
                "إدارة الخامات المتاحة في المنتجات مع الأرشفة بدل الحذف.",
                "Manage product materials using archive/reactivate instead of destructive deletion.",
            ),
        },
    )


@staff_required
def material_create(request):
    require_permission(request.user, "manage_master_data")
    form = MaterialManagementForm(
        request.POST or None,
        request.FILES or None,
        language_code=request.LANGUAGE_CODE,
    )
    if request.method == "POST" and form.is_valid():
        try:
            obj = _save_master_data_form(form, kind="materials")
        except Exception:
            form.add_error(
                "image",
                "تعذر رفع الصورة إلى Cloudinary. حاول مرة أخرى."
                if request.LANGUAGE_CODE != "en"
                else "Unable to upload the image to Cloudinary. Please try again.",
            )
        else:
            audit(
                request,
                "material_created",
                obj,
                new={
                    "name_ar": obj.name_ar,
                    "name_en": obj.name_en,
                    "is_active": obj.is_active,
                    "has_image": bool(obj.image_public_id),
                },
            )
            return redirect(MANAGEMENT_MATERIALS_URL)
    return render(
        request,
        MANAGEMENT_FORM_TEMPLATE,
        {
            "form": form,
            "title": "Create Material"
            if request.LANGUAGE_CODE == "en"
            else "إضافة خامة",
            "page_description": "The URL slug and Cloudinary path are generated by the server."
            if request.LANGUAGE_CODE == "en"
            else "يُنشئ النظام الرابط الداخلي ومسار Cloudinary تلقائيًا.",
            "cancel_url_name": MANAGEMENT_MATERIALS_URL,
            "current_image_url": "",
        },
    )


@staff_required
def material_edit(request, public_id):
    require_permission(request.user, "manage_master_data")
    obj = get_object_or_404(Material, public_id=public_id)
    form = MaterialManagementForm(
        request.POST or None,
        request.FILES or None,
        instance=obj,
        language_code=request.LANGUAGE_CODE,
    )
    if request.method == "POST" and form.is_valid():
        old = {
            "name_ar": obj.name_ar,
            "name_en": obj.name_en,
            "is_active": obj.is_active,
            "sort_order": obj.sort_order,
            "has_image": bool(obj.image_public_id),
        }
        try:
            updated = _save_master_data_form(form, kind="materials")
        except Exception:
            form.add_error(
                "image",
                "تعذر تحديث الصورة في Cloudinary. حاول مرة أخرى."
                if request.LANGUAGE_CODE != "en"
                else "Unable to update the Cloudinary image. Please try again.",
            )
        else:
            audit(
                request,
                "material_updated",
                updated,
                old=old,
                new={
                    "name_ar": updated.name_ar,
                    "name_en": updated.name_en,
                    "is_active": updated.is_active,
                    "sort_order": updated.sort_order,
                    "has_image": bool(updated.image_public_id),
                },
            )
            return redirect(MANAGEMENT_MATERIALS_URL)
    return render(
        request,
        MANAGEMENT_FORM_TEMPLATE,
        {
            "form": form,
            "title": "Edit Material"
            if request.LANGUAGE_CODE == "en"
            else "تعديل الخامة",
            "page_description": obj.slug,
            "cancel_url_name": MANAGEMENT_MATERIALS_URL,
            "current_image_url": obj.image_url,
        },
    )


@staff_required
@require_POST
def material_toggle(request, public_id):
    require_permission(request.user, "manage_master_data")
    obj = get_object_or_404(Material, public_id=public_id)
    old = obj.is_active
    with transaction.atomic():
        obj.is_active = not obj.is_active
        obj.save(update_fields=["is_active"])
        audit(
            request,
            "material_status_changed",
            obj,
            old={"is_active": old},
            new={"is_active": obj.is_active},
        )
    return redirect(MANAGEMENT_MATERIALS_URL)


@staff_required
def products(request):
    require_permission(request.user, "view_products")
    q = _clean_search(request)
    price_source = (request.GET.get("price_source") or "").strip().upper()
    allowed_sources = {"BASE", "PRODUCT", "PROMOTION", "HIGH"}
    if price_source not in allowed_sources:
        price_source = ""

    queryset = (
        Product.objects.select_related("category", "material")
        .prefetch_related("images")
        .order_by("-created_at")
    )
    if q:
        queryset = queryset.filter(
            Q(product_reference__icontains=q)
            | Q(sku__icontains=q)
            | Q(name_ar__icontains=q)
            | Q(name_en__icontains=q)
            | Q(category__name_ar__icontains=q)
            | Q(category__name_en__icontains=q)
        )

    # Price-source filtering is deliberately based on the central pricing engine,
    # never on a duplicated SQL approximation. This keeps expired promotions out
    # automatically and preserves the non-stacking "best price wins" rule.
    all_products = attach_offer_snapshots(list(queryset))
    for product in all_products:
        snap = product.offer_snapshot
        base = Decimal(snap["base_price"])
        final = Decimal(snap["final_price"])
        product.price_source = snap["source"]
        product.price_base = base
        product.price_final = final
        product.price_discount_amount = Decimal(snap["discount_amount"])
        product.price_discount_percent = (
            ((base - final) / base * Decimal("100")).quantize(Decimal("0.01"))
            if base > 0 and final < base
            else Decimal("0.00")
        )
        product.price_promotion = snap.get("promotion")
        product.price_high_warning = product.price_discount_percent > Decimal("15.00")

    if price_source == "HIGH":
        all_products = [p for p in all_products if p.price_high_warning]
    elif price_source:
        all_products = [p for p in all_products if p.price_source == price_source]

    page_obj, pagination_query = _paginate(request, all_products, 25)
    ctx = {
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "pagination_query": pagination_query,
        "q": q,
        "price_source": price_source,
        "result_count": page_obj.paginator.count,
        "last_item_code": _last_public_item_code(),
        "can_create_products": can(request.user, "create_products"),
        "can_edit_products": can(request.user, "edit_products"),
        "can_adjust_inventory": can(request.user, "adjust_inventory"),
        "can_manage_product_images": can(request.user, "manage_product_images"),
        "is_owner": request.user.role == User.Role.OWNER,
        "direct_discount_count": (
            Product.objects.filter(discount_price__isnull=False).count()
            if request.user.role == User.Role.OWNER
            else 0
        ),
        "discount_cleanup_result": request.session.pop("discount_cleanup_result", None),
        **page_copy(
            request,
            "إدارة المنتجات",
            "Products Management",
            "ابحث بالمرجع أو SKU أو الاسم، وراجع مصدر السعر والخصم الحالي لكل قطعة.",
            "Search products and review the current server-selected price and discount source.",
        ),
    }
    return render(request, "management/products.html", ctx)


@staff_required
def product_create(request):
    require_permission(request.user, "create_products")
    form = ManagementProductForm(
        request.POST or None,
        allow_status=False,
        allow_verification=request.user.role == User.Role.OWNER,
    )
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.cost_price = 0
        obj.selling_price = 0
        obj.status = Product.Status.DRAFT
        obj.save()
        audit(
            request,
            "product_created",
            obj,
            new={"product_reference": obj.product_reference, "sku": obj.sku},
        )
        messages.success(
            request,
            (
                f"Product created successfully. Item code: {obj.sku}"
                if request.LANGUAGE_CODE == "en"
                else f"تم إنشاء المنتج بنجاح. رقم القطعة: {obj.sku}"
            ),
        )
        if request.user.role == User.Role.OWNER:
            return redirect("core:management_pricing", public_id=obj.public_id)
        return redirect(MANAGEMENT_PRODUCTS_URL)
    return render(
        request,
        "management/product_form.html",
        {
            "form": form,
            "title": "Create Product"
            if request.LANGUAGE_CODE == "en"
            else "إنشاء منتج جديد",
            "page_description": "The product is created as Draft. The permanent reference and SKU are generated automatically; owner-only pricing is set after saving."
            if request.LANGUAGE_CODE == "en"
            else "يُنشأ المنتج كمسودة، ويولّد النظام المرجع الثابت وSKU تلقائيًا. بعد الحفظ يحدد المالك التكلفة وسعر البيع والخصم في صفحة منفصلة.",
            "last_item_code": _last_public_item_code(),
            "is_create": True,
        },
    )


@staff_required
def product_edit(request, public_id):
    require_permission(request.user, "edit_products")
    product = get_object_or_404(Product, public_id=public_id)
    form = ManagementProductForm(
        request.POST or None,
        instance=product,
        allow_verification=request.user.role == User.Role.OWNER,
    )
    if request.method == "POST" and form.is_valid():
        old = {
            "name_ar": product.name_ar,
            "status": product.status,
            "verification_status": product.verification_status,
        }
        obj = form.save()
        audit(
            request,
            "product_updated",
            obj,
            old,
            {
                "name_ar": obj.name_ar,
                "status": obj.status,
                "verification_status": obj.verification_status,
            },
        )
        return redirect(MANAGEMENT_PRODUCTS_URL)
    return render(
        request,
        "management/product_form.html",
        {
            "form": form,
            "product": product,
            "title": "Edit Product"
            if request.LANGUAGE_CODE == "en"
            else "تعديل المنتج",
            "page_description": f"{product.product_reference} · {product.sku}",
            "is_create": False,
        },
    )


@staff_required
def product_images(request, public_id):
    require_permission(request.user, "manage_product_images")
    product = get_object_or_404(Product, public_id=public_id)
    form = ProductImageUploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        try:
            created = attach_product_images(product, form.cleaned_data["images"])
        except Exception:
            # Do not expose Cloudinary/API implementation details to the browser.
            form.add_error(
                "images",
                "تعذر رفع الصور. تحقق من الملفات وإعداد Cloudinary ثم حاول مرة أخرى."
                if request.LANGUAGE_CODE != "en"
                else "Unable to upload the images. Check the files and Cloudinary configuration, then try again.",
            )
        else:
            audit(
                request,
                "product_images_uploaded",
                product,
                new={
                    "count": len(created),
                    "image_public_ids": [str(image.public_id) for image in created],
                },
            )
            return redirect(
                MANAGEMENT_PRODUCT_IMAGES_URL, public_id=product.public_id
            )

    images = product.images.all()
    return render(
        request,
        "management/product_images.html",
        {
            "product": product,
            "images": images,
            "form": form,
            "max_images": settings.PRODUCT_IMAGE_MAX_COUNT,
            "remaining_images": max(
                settings.PRODUCT_IMAGE_MAX_COUNT - images.count(), 0
            ),
            "max_image_mb": settings.PRODUCT_IMAGE_MAX_BYTES // (1024 * 1024),
            **page_copy(
                request,
                "صور المنتج",
                "Product Images",
                f"{product.product_reference} · ارفع الصور وحدد الرئيسية ورتّب ظهورها.",
                f"{product.product_reference} · Upload, order and choose the primary product image.",
            ),
        },
    )


@staff_required
@require_POST
def product_image_update(request, public_id, image_public_id):
    require_permission(request.user, "manage_product_images")
    product = get_object_or_404(Product, public_id=public_id)
    image = get_object_or_404(ProductImage, public_id=image_public_id, product=product)
    form = ProductImageMetadataForm(request.POST)
    if not form.is_valid():
        return redirect(MANAGEMENT_PRODUCT_IMAGES_URL, public_id=product.public_id)

    old = {
        "alt_text_ar": image.alt_text_ar,
        "alt_text_en": image.alt_text_en,
        "sort_order": image.sort_order,
    }
    update_image_metadata(
        image,
        alt_text_ar=form.cleaned_data["alt_text_ar"],
        alt_text_en=form.cleaned_data["alt_text_en"],
        sort_order=form.cleaned_data["sort_order"],
    )
    audit(
        request,
        "product_image_updated",
        product,
        old=old,
        new={
            "image": str(image.public_id),
            "alt_text_ar": image.alt_text_ar,
            "alt_text_en": image.alt_text_en,
            "sort_order": image.sort_order,
        },
    )
    return redirect(MANAGEMENT_PRODUCT_IMAGES_URL, public_id=product.public_id)


@staff_required
@require_POST
def product_image_primary(request, public_id, image_public_id):
    require_permission(request.user, "manage_product_images")
    product = get_object_or_404(Product, public_id=public_id)
    image = get_object_or_404(ProductImage, public_id=image_public_id, product=product)
    set_primary_image(image)
    audit(
        request,
        "product_primary_image_changed",
        product,
        new={"image": str(image.public_id)},
    )
    return redirect(MANAGEMENT_PRODUCT_IMAGES_URL, public_id=product.public_id)


@staff_required
@require_POST
def product_image_delete(request, public_id, image_public_id):
    require_permission(request.user, "manage_product_images")
    product = get_object_or_404(Product, public_id=public_id)
    image = get_object_or_404(ProductImage, public_id=image_public_id, product=product)
    image_id = str(image.public_id)
    try:
        delete_product_image(image)
    except Exception:
        # Preserve the DB record if Cloudinary did not confirm deletion.
        return render(
            request,
            "management/product_image_delete_error.html",
            {
                "product": product,
                "page_title": "تعذر حذف الصورة"
                if request.LANGUAGE_CODE != "en"
                else "Image deletion failed",
            },
            status=502,
        )

    audit(
        request,
        "product_image_deleted",
        product,
        old={"image": image_id},
    )
    return redirect(MANAGEMENT_PRODUCT_IMAGES_URL, public_id=product.public_id)


@staff_required
def pricing(request, public_id):
    require_owner(request.user)
    product = get_object_or_404(Product, public_id=public_id)
    form = PricingForm(request.POST or None, instance=product, language_code=request.LANGUAGE_CODE)
    if request.method == "POST" and form.is_valid():
        old = {
            "cost_price": str(product.cost_price),
            "selling_price": str(product.selling_price),
            "discount_price": str(product.discount_price),
        }
        obj = form.save()
        reason = (form.cleaned_data.get("discount_reason") or "").strip()
        audit(
            request,
            "pricing_changed",
            obj,
            old,
            {
                "cost_price": str(obj.cost_price),
                "selling_price": str(obj.selling_price),
                "discount_price": str(obj.discount_price),
                "discount_reason": reason,
            },
            metadata={
                "discount_source": "PRODUCT" if obj.discount_price is not None else "BASE",
                "high_discount_confirmed": bool(form.cleaned_data.get("confirm_high_discount")),
            },
        )
        return redirect(MANAGEMENT_PRODUCTS_URL)

    return render(
        request,
        MANAGEMENT_FORM_TEMPLATE,
        {
            "form": form,
            "title": "Owner Pricing"
            if request.LANGUAGE_CODE == "en"
            else "التكلفة والتسعير — للمالك فقط",
            "page_description": f"{product.product_reference} · {product.sku}",
            "product": product,
        },
    )


@staff_required
def product_pricing_history(request, public_id):
    require_owner(request.user)
    product = get_object_or_404(Product, public_id=public_id)
    pricing_history = list(
        AuditLog.objects.filter(
            object_type="Product",
            object_reference=str(product.product_reference),
            action__in=["pricing_changed", "direct_discount_cleared"],
        ).order_by("-created_at")[:50]
    )
    return render(
        request,
        "management/pricing_history.html",
        {
            "product": product,
            "pricing_history": pricing_history,
            **page_copy(
                request,
                f"سجل التسعير — {product.sku}",
                f"Pricing History — {product.sku}",
                "سجل التغييرات المتوفر للخصم والتسعير لهذه القطعة.",
                "Available pricing and direct-discount audit history for this product.",
            ),
        },
    )


@staff_required
@require_POST
def clear_direct_discount(request, public_id):
    """Owner-only removal of one product's persistent direct discount."""
    require_owner(request.user)
    with transaction.atomic():
        product = get_object_or_404(
            Product.objects.select_for_update(), public_id=public_id
        )
        old_discount = product.discount_price
        if old_discount is not None:
            product.discount_price = None
            product.save(update_fields=["discount_price", "updated_at"])
            audit(
                request,
                "direct_discount_cleared",
                product,
                old={"discount_price": str(old_discount)},
                new={"discount_price": None},
                metadata={"reason": (request.POST.get("reason") or "Owner cleared direct discount")[:200]},
            )
    messages.success(request, "تم إلغاء الخصم المباشر. سيستخدم النظام السعر الأساسي أو العرض النشط تلقائيًا.")
    return redirect(MANAGEMENT_PRODUCTS_URL)


@staff_required
@require_POST
def clear_all_direct_discounts(request):
    """Owner-only, explicit bulk cleanup. Promotions are not modified."""
    require_owner(request.user)
    if request.POST.get("confirm") != "CLEAR_ALL_DIRECT_DISCOUNTS":
        messages.error(request, "لم يتم التنفيذ: يلزم تأكيد صريح لمسح جميع الخصومات المباشرة.")
        return redirect(MANAGEMENT_PRODUCTS_URL)

    reason = (request.POST.get("reason") or "Owner bulk-cleared legacy direct discounts")[:200]
    with transaction.atomic():
        products = list(
            Product.objects.select_for_update()
            .filter(discount_price__isnull=False)
            .only("id", "public_id", "product_reference", "sku", "discount_price")
        )
        for product in products:
            old_discount = product.discount_price
            product.discount_price = None
            product.save(update_fields=["discount_price", "updated_at"])
            audit(
                request,
                "direct_discount_cleared",
                product,
                old={"discount_price": str(old_discount)},
                new={"discount_price": None},
                metadata={"reason": reason, "bulk": True},
            )
    request.session["discount_cleanup_result"] = {
        "cleared_count": len(products),
        "promotions_modified": 0,
    }
    return redirect(MANAGEMENT_PRODUCTS_URL)


@staff_required
def inventory_adjust(request, public_id):
    require_permission(request.user, "adjust_inventory")
    product = get_object_or_404(Product, public_id=public_id)
    form = InventoryAdjustmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            locked = Product.objects.select_for_update().get(pk=product.pk)
            before = locked.available_quantity
            after = before + form.cleaned_data["delta"]
            if after < locked.reserved_quantity or after < 0:
                form.add_error(
                    "delta", "لا يمكن جعل المخزون أقل من الكمية المحجوزة أو أقل من صفر."
                )
            else:
                locked.available_quantity = after
                locked.save(update_fields=["available_quantity", "updated_at"])
                InventoryTransaction.objects.create(
                    product=locked,
                    movement_type=InventoryTransaction.Type.ADJUST,
                    quantity=form.cleaned_data["delta"],
                    before_quantity=before,
                    after_quantity=after,
                    actor=request.user,
                    reason=form.cleaned_data["reason"],
                )
                audit(
                    request,
                    "inventory_adjusted",
                    locked,
                    {"available_quantity": before},
                    {
                        "available_quantity": after,
                        "reason": form.cleaned_data["reason"],
                    },
                )
                return redirect(MANAGEMENT_PRODUCTS_URL)
    return render(
        request,
        MANAGEMENT_FORM_TEMPLATE,
        {
            "form": form,
            "title": f"Inventory — {product.sku}"
            if request.LANGUAGE_CODE == "en"
            else f"تعديل مخزون {product.sku}",
            "page_description": "Inventory changes are recorded in the audit ledger."
            if request.LANGUAGE_CODE == "en"
            else "كل تعديل للمخزون يتم تسجيله في سجل التدقيق.",
        },
    )


@staff_required
def orders_list(request):
    require_permission(request.user, "view_orders")
    q = _clean_search(request)
    queryset = Order.objects.select_related("user").order_by("-created_at")
    stage = (request.GET.get("stage") or "").strip().lower()
    requested_status = (request.GET.get("status") or "").strip().upper()
    allowed_statuses = {value for value, _label in Order.Status.choices}
    status_filter = requested_status if requested_status in allowed_statuses else ""
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if stage == "delivery":
        queryset = queryset.filter(
            payment_status=Order.PaymentStatus.PAID,
            status__in=[
                Order.Status.CONFIRMED,
                Order.Status.PREPARING,
                Order.Status.READY,
                Order.Status.SHIPPED,
                Order.Status.OUT_FOR_DELIVERY,
            ],
        )
    if q:
        queryset = queryset.filter(
            Q(reference__icontains=q)
            | Q(customer_name__icontains=q)
            | Q(customer_phone__icontains=q)
        )
    page_obj, pagination_query = _paginate(request, queryset, 25)
    ctx = {
        "orders": page_obj.object_list,
        "page_obj": page_obj,
        "pagination_query": pagination_query,
        "q": q,
        "stage": stage,
        "status_filter": status_filter,
        "order_status_choices": Order.Status.choices,
        "result_count": page_obj.paginator.count,
        **page_copy(
            request,
            "إدارة الطلبات",
            "Orders Management",
            "متابعة الطلبات مع البحث برقم الطلب أو اسم العميل أو الهاتف.",
            "Review orders with search by order reference, customer name or phone.",
        ),
    }
    return render(request, "management/orders.html", ctx)


@staff_required
def order_manage(request, public_id):
    require_permission(request.user, "view_orders")
    order = get_object_or_404(
        Order.objects.select_related("manual_paid_by").prefetch_related(
            "items", "payment_attempts"
        ),
        public_id=public_id,
    )
    latest_attempt = order.payment_attempts.order_by("-created_at").first()
    is_stripe_order = order.payment_method == Order.PaymentMethod.STRIPE or (
        order.payment_method == Order.PaymentMethod.UNSET and latest_attempt is not None
    )

    status_form = OrderStatusForm(
        request.POST or None,
        prefix="order",
        order=order,
        initial={"status": order.status},
    )
    payment_form = PaymentStatusForm(
        request.POST or None,
        prefix="pay",
        initial={"payment_status": order.payment_status},
    )
    manual_payment_form = ManualPaymentConfirmationForm(
        request.POST or None, prefix="manual"
    )
    reservation_extension_form = ReservationExtensionForm(
        request.POST or None, prefix="extend", language_code=request.LANGUAGE_CODE
    )
    shipping_form = ShippingDetailsForm(
        request.POST or None,
        prefix="ship",
        initial={
            "shipping_carrier": order.shipping_carrier,
            "tracking_number": order.tracking_number,
            "tracking_url": order.tracking_url,
        },
        language_code=request.LANGUAGE_CODE,
    )

    hand_to_hand_form = HandToHandDeliveryForm(
        request.POST or None,
        prefix="handover",
        language_code=request.LANGUAGE_CODE,
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "complete_bead_adjustment":
            item_id = request.POST.get("item_id")
            with transaction.atomic():
                bead_item = get_object_or_404(
                    OrderItem.objects.select_for_update(),
                    pk=item_id,
                    order=order,
                )
                if (
                    not bead_item.requested_bead_count_snapshot
                    or not bead_item.original_bead_count_snapshot
                    or bead_item.requested_bead_count_snapshot >= bead_item.original_bead_count_snapshot
                ):
                    raise PermissionDenied("No bead adjustment is required for this item.")
                if not bead_item.bead_adjustment_completed_at:
                    bead_item.bead_adjustment_completed_at = timezone.now()
                    bead_item.bead_adjustment_completed_by = request.user
                    bead_item.save(update_fields=["bead_adjustment_completed_at", "bead_adjustment_completed_by"])
                    audit(
                        request,
                        "bead_adjustment_completed",
                        bead_item,
                        new={
                            "original_bead_count": bead_item.original_bead_count_snapshot,
                            "requested_bead_count": bead_item.requested_bead_count_snapshot,
                        },
                    )
            messages.success(request, "تم تأكيد اكتمال ضبط عدد الخرز.")
            return redirect(MANAGEMENT_ORDER_URL, public_id=order.public_id)

        if action == "status" and status_form.is_valid():
            target = status_form.cleaned_data["status"]
            if target in {Order.Status.READY, Order.Status.SHIPPED, Order.Status.OUT_FOR_DELIVERY, Order.Status.DELIVERED}:
                pending_beads = order.items.filter(
                    requested_bead_count_snapshot__isnull=False,
                    bead_adjustment_completed_at__isnull=True,
                ).exclude(
                    requested_bead_count_snapshot=models.F("original_bead_count_snapshot")
                ).exists()
                if pending_beads:
                    messages.error(request, "لا يمكن متابعة التسليم قبل تأكيد اكتمال ضبط عدد الخرز.")
                    return redirect(MANAGEMENT_ORDER_URL, public_id=order.public_id)
            with transaction.atomic():
                locked = Order.objects.select_for_update().get(pk=order.pk)
                allowed_transitions = {
                    Order.Status.PENDING: {Order.Status.CANCELLED},
                    Order.Status.CONFIRMED: {
                        Order.Status.PREPARING,
                        Order.Status.CANCELLED,
                    },
                    Order.Status.PREPARING: {
                        Order.Status.READY,
                        Order.Status.CANCELLED,
                    },
                    Order.Status.READY: {Order.Status.SHIPPED, Order.Status.CANCELLED},
                    Order.Status.SHIPPED: {
                        Order.Status.OUT_FOR_DELIVERY,
                        Order.Status.DELIVERED,
                        Order.Status.RETURNED,
                    },
                    Order.Status.OUT_FOR_DELIVERY: {
                        Order.Status.DELIVERED,
                        Order.Status.RETURNED,
                    },
                    Order.Status.DELIVERED: {Order.Status.RETURNED},
                    Order.Status.CANCELLED: set(),
                    Order.Status.RETURNED: set(),
                }
                if target != locked.status and target not in allowed_transitions.get(
                    locked.status, set()
                ):
                    raise PermissionDenied("Invalid order status transition.")
                if (
                    target == Order.Status.CANCELLED
                    and locked.payment_status == Order.PaymentStatus.PAID
                ):
                    raise PermissionDenied(
                        "Paid orders require the dedicated refund/return workflow."
                    )
                if (
                    target
                    not in {
                        locked.status,
                        Order.Status.CANCELLED,
                        Order.Status.RETURNED,
                    }
                    and locked.payment_status != Order.PaymentStatus.PAID
                ):
                    raise PermissionDenied(
                        "Order must be paid before fulfilment can continue."
                    )
                if (
                    target == Order.Status.SHIPPED
                    and not locked.shipping_carrier.strip()
                ):
                    messages.error(
                        request,
                        "أدخل شركة التوصيل قبل تحويل الطلب إلى تم الشحن."
                        if request.LANGUAGE_CODE != "en"
                        else "Add the shipping carrier before marking the order as shipped.",
                    )
                    return redirect(MANAGEMENT_ORDER_URL, public_id=locked.public_id)

                permission_map = {
                    Order.Status.PREPARING: "prepare_orders",
                    Order.Status.READY: "prepare_orders",
                    Order.Status.SHIPPED: "ship_orders",
                    Order.Status.OUT_FOR_DELIVERY: "ship_orders",
                    Order.Status.DELIVERED: "ship_orders",
                    Order.Status.CANCELLED: "cancel_orders",
                    Order.Status.RETURNED: "cancel_orders",
                }
                if target != locked.status:
                    require_permission(request.user, permission_map[target])
                old = locked.status
                if target == old:
                    return redirect(MANAGEMENT_ORDER_URL, public_id=locked.public_id)
                if target == Order.Status.CANCELLED:
                    release_order_reservations(
                        locked, request.user, reason="Management order cancellation"
                    )
                locked.status = target
                update_fields = ["status", "updated_at"]
                if target == Order.Status.SHIPPED and locked.shipped_at is None:
                    locked.shipped_at = timezone.now()
                    update_fields.append("shipped_at")
                if (
                    target == Order.Status.OUT_FOR_DELIVERY
                    and locked.out_for_delivery_at is None
                ):
                    locked.out_for_delivery_at = timezone.now()
                    update_fields.append("out_for_delivery_at")
                if target == Order.Status.DELIVERED and locked.delivered_at is None:
                    locked.delivered_at = timezone.now()
                    update_fields.append("delivered_at")
                locked.save(update_fields=update_fields)
                OrderTimelineEvent.objects.create(
                    order=locked,
                    kind=OrderTimelineEvent.Kind.STATUS_CHANGED,
                    label_ar="تم تحديث حالة الطلب",
                    label_en="Order status updated",
                    actor=request.user,
                    from_value=old,
                    to_value=target,
                )
                audit(
                    request,
                    "order_status_changed",
                    locked,
                    {"status": old},
                    {"status": target},
                )
                transaction.on_commit(
                    lambda order_id=locked.pk, status=target: __import__(
                        "orders.services.notification_service",
                        fromlist=["notify_order_status"],
                    ).notify_order_status(order_id, status),
                    robust=True,
                )
            return redirect(MANAGEMENT_ORDER_URL, public_id=order.public_id)

        if action == "extend_reservation" and reservation_extension_form.is_valid():
            require_permission(request.user, "extend_reservations")
            minutes = reservation_extension_form.cleaned_data["minutes"]
            with transaction.atomic():
                locked = Order.objects.select_for_update().get(pk=order.pk)
                if locked.payment_status == Order.PaymentStatus.PAID:
                    raise PermissionDenied(
                        "Paid orders do not have an extendable checkout reservation."
                    )
                if locked.status in {
                    Order.Status.CANCELLED,
                    Order.Status.RETURNED,
                    Order.Status.DELIVERED,
                }:
                    raise PermissionDenied(
                        "This order cannot have its reservation extended."
                    )
                active_attempt = (
                    locked.payment_attempts.select_for_update()
                    .filter(
                        status__in=[
                            PaymentAttempt.Status.CREATING,
                            PaymentAttempt.Status.OPEN,
                            PaymentAttempt.Status.PROCESSING,
                        ],
                        expires_at__gt=timezone.now(),
                    )
                    .exists()
                )
                if active_attempt:
                    raise PermissionDenied(
                        "An active Stripe payment session already controls the provider payment window."
                    )
                reservations = list(
                    Reservation.objects.select_for_update()
                    .filter(
                        order=locked, released_at__isnull=True, consumed_at__isnull=True
                    )
                    .order_by("expires_at", "pk")
                )
                if not reservations:
                    raise PermissionDenied(
                        "No active reservation exists for this order."
                    )
                now = timezone.now()
                old_deadline = min(r.expires_at for r in reservations)
                if old_deadline <= now:
                    raise PermissionDenied(
                        "Expired reservations must not be revived from management."
                    )
                new_deadline = old_deadline + timezone.timedelta(minutes=minutes)
                for reservation in reservations:
                    reservation.expires_at = new_deadline
                    reservation.save(update_fields=["expires_at"])
                OrderTimelineEvent.objects.create(
                    order=locked,
                    kind=OrderTimelineEvent.Kind.NOTE,
                    label_ar=f"تم تمديد مهلة الحجز {minutes} دقيقة بواسطة الإدارة",
                    label_en=f"Reservation extended by management for {minutes} minutes",
                    actor=request.user,
                    from_value=old_deadline.isoformat(),
                    to_value=new_deadline.isoformat(),
                )
                audit(
                    request,
                    "order_reservation_extended",
                    locked,
                    {"reservation_deadline": old_deadline.isoformat()},
                    {
                        "reservation_deadline": new_deadline.isoformat(),
                        "minutes": minutes,
                    },
                )
            messages.success(
                request,
                f"تم تمديد حجز الطلب {minutes} دقيقة."
                if request.LANGUAGE_CODE != "en"
                else f"Order reservation extended by {minutes} minutes.",
            )
            return redirect(MANAGEMENT_ORDER_URL, public_id=order.public_id)

        if action == "hand_to_hand" and hand_to_hand_form.is_valid():
            require_permission(request.user, "ship_orders")
            with transaction.atomic():
                locked = Order.objects.select_for_update().get(pk=order.pk)
                if locked.status in {Order.Status.CANCELLED, Order.Status.RETURNED}:
                    raise PermissionDenied("Cancelled or returned orders cannot be handed over.")
                if locked.hand_to_hand_at is not None:
                    return redirect(MANAGEMENT_ORDER_URL, public_id=locked.public_id)

                # A direct deferred sale is intentionally allowed: the physical item
                # may be handed over while the financial receivable remains open.
                if (
                    locked.payment_status != Order.PaymentStatus.PAID
                    and not (
                        locked.sale_channel == Order.SaleChannel.DIRECT
                        and locked.payment_method == Order.PaymentMethod.DEFERRED
                    )
                ):
                    raise PermissionDenied(
                        "Unpaid non-deferred orders cannot be handed over."
                    )

                old_status = locked.status
                now = timezone.now()
                locked.delivery_method = Order.DeliveryMethod.HAND_TO_HAND
                locked.hand_to_hand_at = now
                locked.hand_to_hand_by = request.user
                locked.status = Order.Status.DELIVERED
                if locked.delivered_at is None:
                    locked.delivered_at = now
                locked.save(update_fields=[
                    "delivery_method",
                    "hand_to_hand_at",
                    "hand_to_hand_by",
                    "status",
                    "delivered_at",
                    "updated_at",
                ])
                note = (hand_to_hand_form.cleaned_data.get("note") or "").strip()
                OrderTimelineEvent.objects.create(
                    order=locked,
                    kind=OrderTimelineEvent.Kind.STATUS_CHANGED,
                    label_ar="تم تسليم القطعة يدًا بيد للمشتري",
                    label_en="Item handed directly to the buyer",
                    actor=request.user,
                    from_value=old_status,
                    to_value=Order.Status.DELIVERED,
                )
                audit(
                    request,
                    "order_hand_to_hand_delivered",
                    locked,
                    {"status": old_status},
                    {
                        "status": locked.status,
                        "delivery_method": locked.delivery_method,
                        "hand_to_hand_at": now.isoformat(),
                        "note": note[:300],
                    },
                )
            messages.success(
                request,
                "تم تسجيل الاستلام يدًا بيد."
                if request.LANGUAGE_CODE != "en"
                else "Hand-to-hand delivery recorded.",
            )
            return redirect(MANAGEMENT_ORDER_URL, public_id=order.public_id)

        if action == "shipping" and shipping_form.is_valid():
            require_permission(request.user, "ship_orders")
            with transaction.atomic():
                locked = Order.objects.select_for_update().get(pk=order.pk)
                if (
                    locked.payment_status != Order.PaymentStatus.PAID
                    or locked.status
                    in {
                        Order.Status.PENDING,
                        Order.Status.CANCELLED,
                        Order.Status.RETURNED,
                    }
                ):
                    raise PermissionDenied(
                        "Delivery details can only be changed for paid active orders."
                    )
                old = {
                    "shipping_carrier": locked.shipping_carrier,
                    "tracking_number": locked.tracking_number,
                    "tracking_url": locked.tracking_url,
                }
                locked.shipping_carrier = shipping_form.cleaned_data[
                    "shipping_carrier"
                ].strip()
                locked.tracking_number = shipping_form.cleaned_data[
                    "tracking_number"
                ].strip()
                locked.tracking_url = shipping_form.cleaned_data["tracking_url"].strip()
                locked.save(
                    update_fields=[
                        "shipping_carrier",
                        "tracking_number",
                        "tracking_url",
                        "updated_at",
                    ]
                )
                OrderTimelineEvent.objects.create(
                    order=locked,
                    kind=OrderTimelineEvent.Kind.NOTE,
                    label_ar="تم تحديث بيانات التوصيل",
                    label_en="Delivery details updated",
                    actor=request.user,
                )
                audit(
                    request,
                    "order_shipping_changed",
                    locked,
                    old,
                    {
                        "shipping_carrier": locked.shipping_carrier,
                        "tracking_number": locked.tracking_number,
                    },
                )
            return redirect(MANAGEMENT_ORDER_URL, public_id=order.public_id)

        if action == "manual_paid" and manual_payment_form.is_valid():
            require_permission(request.user, "mark_paid")
            with transaction.atomic():
                locked = Order.objects.select_for_update().get(pk=order.pk)
                attempts = locked.payment_attempts.select_for_update()
                if (
                    locked.payment_method == Order.PaymentMethod.STRIPE
                    or attempts.filter(status=PaymentAttempt.Status.PAID).exists()
                ):
                    raise PermissionDenied(
                        "Stripe payments cannot be confirmed manually."
                    )
                if attempts.filter(
                    status__in=[
                        PaymentAttempt.Status.CREATING,
                        PaymentAttempt.Status.OPEN,
                        PaymentAttempt.Status.PROCESSING,
                    ]
                ).exists():
                    raise PermissionDenied(
                        "An active Stripe payment attempt exists for this order."
                    )
                if locked.payment_status == Order.PaymentStatus.PAID:
                    return redirect(MANAGEMENT_ORDER_URL, public_id=locked.public_id)
                if locked.status in {Order.Status.CANCELLED, Order.Status.RETURNED}:
                    raise PermissionDenied(
                        "Cancelled or returned orders cannot be marked paid."
                    )

                old_payment = locked.payment_status
                old_status = locked.status
                consume_order_reservations(locked, request.user)
                locked.payment_method = Order.PaymentMethod.MANUAL
                locked.payment_status = Order.PaymentStatus.PAID
                if locked.status == Order.Status.PENDING:
                    locked.status = Order.Status.CONFIRMED
                locked.manual_paid_at = timezone.now()
                locked.manual_paid_by = request.user
                locked.save(
                    update_fields=[
                        "payment_method",
                        "payment_status",
                        "status",
                        "manual_paid_at",
                        "manual_paid_by",
                        "updated_at",
                    ]
                )
                OrderTimelineEvent.objects.create(
                    order=locked,
                    kind=OrderTimelineEvent.Kind.PAYMENT_CHANGED,
                    label_ar="تم تأكيد استلام الدفعة اليدوية",
                    label_en="Manual payment receipt confirmed",
                    actor=request.user,
                    from_value=old_payment,
                    to_value=Order.PaymentStatus.PAID,
                )
                if old_status != locked.status:
                    OrderTimelineEvent.objects.create(
                        order=locked,
                        kind=OrderTimelineEvent.Kind.STATUS_CHANGED,
                        label_ar="تم تأكيد الطلب بعد استلام الدفعة",
                        label_en="Order confirmed after payment receipt",
                        actor=request.user,
                        from_value=old_status,
                        to_value=locked.status,
                    )
                transaction.on_commit(
                    lambda order_id=locked.pk: __import__(
                        "orders.services.notification_service",
                        fromlist=["notify_payment_received"],
                    ).notify_payment_received(order_id),
                    robust=True,
                )
                audit(
                    request,
                    "manual_payment_confirmed",
                    locked,
                    {"payment_status": old_payment, "status": old_status},
                    {
                        "payment_status": locked.payment_status,
                        "status": locked.status,
                        "payment_method": locked.payment_method,
                    },
                )
            messages.success(
                request,
                "تم تأكيد استلام المبلغ وتأكيد الطلب."
                if request.LANGUAGE_CODE != "en"
                else "Payment receipt and order confirmed.",
            )
            return redirect(MANAGEMENT_ORDER_URL, public_id=order.public_id)

        if action == "reconcile_stripe":
            require_permission(request.user, "mark_paid")
            if not is_stripe_order:
                raise PermissionDenied("This order is not associated with Stripe.")
            try:
                result = reconcile_order_payment(order)
            except Exception:
                messages.error(
                    request,
                    "تعذر التحقق من Stripe الآن."
                    if request.LANGUAGE_CODE != "en"
                    else "Stripe verification is temporarily unavailable.",
                )
            else:
                messages.success(
                    request,
                    ("تم التحقق من Stripe: " + result)
                    if request.LANGUAGE_CODE != "en"
                    else ("Stripe verification: " + result),
                )
            return redirect(MANAGEMENT_ORDER_URL, public_id=order.public_id)

        # Legacy generic payment-status mutation is intentionally disabled.
        # Stripe status is provider-controlled; manual payments use the explicit
        # confirmation workflow above so stock conversion cannot be bypassed.
        if action == "payment" and payment_form.is_valid():
            target = payment_form.cleaned_data["payment_status"]
            if target in {Order.PaymentStatus.REFUNDED, Order.PaymentStatus.PARTIAL}:
                require_owner(request.user)
            else:
                require_permission(request.user, "mark_payment_pending")
            raise PermissionDenied(
                "Generic payment status changes are disabled; use the dedicated payment workflow."
            )

    # Always re-read the persisted state after any provider/background update so
    # the management page never renders a stale default form value.
    order.refresh_from_db()
    latest_attempt = order.payment_attempts.order_by("-created_at").first()
    is_stripe_order = order.payment_method == Order.PaymentMethod.STRIPE or (
        order.payment_method == Order.PaymentMethod.UNSET and latest_attempt is not None
    )
    timeline = (
        order.timeline.select_related("actor").all()
        if can(request.user, "view_order_timeline")
        else ()
    )
    can_mark_paid = can(request.user, "mark_paid")
    next_status_map = {
        Order.Status.PENDING: [Order.Status.CANCELLED],
        Order.Status.CONFIRMED: [Order.Status.PREPARING, Order.Status.CANCELLED],
        Order.Status.PREPARING: [Order.Status.READY, Order.Status.CANCELLED],
        Order.Status.READY: [Order.Status.SHIPPED, Order.Status.CANCELLED],
        Order.Status.SHIPPED: [
            Order.Status.OUT_FOR_DELIVERY,
            Order.Status.DELIVERED,
            Order.Status.RETURNED,
        ],
        Order.Status.OUT_FOR_DELIVERY: [Order.Status.DELIVERED, Order.Status.RETURNED],
        Order.Status.DELIVERED: [Order.Status.RETURNED],
        Order.Status.CANCELLED: [],
        Order.Status.RETURNED: [],
    }
    status_labels = dict(Order.Status.choices)
    raw_status_actions = next_status_map.get(order.status, [])
    if order.payment_status != Order.PaymentStatus.PAID:
        raw_status_actions = [
            value
            for value in raw_status_actions
            if value in {Order.Status.CANCELLED, Order.Status.RETURNED}
        ]
    status_actions = [(value, status_labels[value]) for value in raw_status_actions]
    deferred_paid = order.direct_payments.aggregate(v=Sum("amount"))["v"] or 0
    deferred_outstanding = max(order.grand_total - deferred_paid, 0)
    can_hand_to_hand = can(request.user, "ship_orders") and (
        order.payment_status == Order.PaymentStatus.PAID
        or (
            order.sale_channel == Order.SaleChannel.DIRECT
            and order.payment_method == Order.PaymentMethod.DEFERRED
        )
    ) and order.status not in {Order.Status.CANCELLED, Order.Status.RETURNED}

    status_rank = {
        Order.Status.PENDING: 0,
        Order.Status.CONFIRMED: 1,
        Order.Status.PREPARING: 1,
        Order.Status.READY: 1,
        Order.Status.SHIPPED: 2,
        Order.Status.OUT_FOR_DELIVERY: 2,
        Order.Status.DELIVERED: 3,
    }
    current_rank = status_rank.get(order.status, 0)
    if order.delivery_method == Order.DeliveryMethod.HAND_TO_HAND:
        tracking_stages = [
            {
                "key": "placed",
                "icon": "icon-orders",
                "label_ar": "تم تسجيل البيع",
                "label_en": "Sale recorded",
                "complete": True,
                "current": False,
            },
            {
                "key": "payment",
                "icon": "icon-wallet",
                "label_ar": "الدفع",
                "label_en": "Payment",
                "complete": order.payment_status == Order.PaymentStatus.PAID,
                "current": order.payment_status != Order.PaymentStatus.PAID,
            },
            {
                "key": "delivered",
                "icon": "icon-user",
                "label_ar": "استلام يدًا بيد",
                "label_en": "Hand-to-hand",
                "complete": order.hand_to_hand_at is not None or order.status == Order.Status.DELIVERED,
                "current": (
                    order.payment_status == Order.PaymentStatus.PAID
                    and order.hand_to_hand_at is None
                    and order.status != Order.Status.DELIVERED
                ),
            },
        ]
    else:
        tracking_stages = [
            {
                "key": "placed",
                "icon": "icon-orders",
                "label_ar": "تم الطلب",
                "label_en": "Order placed",
                "complete": True,
                "current": current_rank == 0,
            },
            {
                "key": "ready",
                "icon": "icon-package",
                "label_ar": "التجهيز",
                "label_en": "Preparing",
                "complete": current_rank >= 1,
                "current": current_rank == 1,
            },
            {
                "key": "transit",
                "icon": "icon-truck",
                "label_ar": "جاري التوصيل",
                "label_en": "In transit",
                "complete": current_rank >= 2,
                "current": current_rank == 2,
            },
            {
                "key": "delivered",
                "icon": "icon-shield",
                "label_ar": "تم التسليم",
                "label_en": "Delivered",
                "complete": current_rank >= 3,
                "current": current_rank == 3,
            },
        ]

    invoice = Invoice.objects.filter(order=order).first()

    return render(
        request,
        "management/order_detail.html",
        {
            "order": order,
            "timeline": timeline,
            "can_view_timeline": can(request.user, "view_order_timeline"),
            "status_form": OrderStatusForm(
                prefix="order", order=order, initial={"status": order.status}
            ),
            "payment_form": payment_form,
            "manual_payment_form": manual_payment_form,
            "reservation_extension_form": ReservationExtensionForm(
                prefix="extend", language_code=request.LANGUAGE_CODE
            ),
            "shipping_form": ShippingDetailsForm(
                prefix="ship",
                initial={
                    "shipping_carrier": order.shipping_carrier,
                    "tracking_number": order.tracking_number,
                    "tracking_url": order.tracking_url,
                },
                language_code=request.LANGUAGE_CODE,
            ),
            "latest_attempt": latest_attempt,
            "is_stripe_order": is_stripe_order,
            "can_mark_paid": can_mark_paid,
            "can_extend_reservations": can(request.user, "extend_reservations"),
            "reservation_deadline": order.reservations.filter(
                released_at__isnull=True, consumed_at__isnull=True
            )
            .order_by("expires_at")
            .values_list("expires_at", flat=True)
            .first(),
            "can_manage_shipping": can(request.user, "ship_orders"),
            "hand_to_hand_form": HandToHandDeliveryForm(
                prefix="handover", language_code=request.LANGUAGE_CODE
            ),
            "can_hand_to_hand": can_hand_to_hand,
            "deferred_paid": deferred_paid,
            "deferred_outstanding": deferred_outstanding,
            "tracking_stages": tracking_stages,
            "invoice": invoice,
            "status_actions": status_actions,
            "payment_source_code": Order.PaymentMethod.STRIPE
            if is_stripe_order
            else order.payment_method,
            **page_copy(
                request,
                f"الطلب {order.reference}",
                f"Order {order.reference}",
                "تفاصيل الطلب والدفع والتوصيل حسب صلاحيات حسابك.",
                "Review order, payment, and delivery using only the actions allowed by your permissions.",
            ),
        },
    )


@staff_required
def customers(request):
    require_permission(request.user, "view_customers")
    q = _clean_search(request)
    queryset = annotate_customer_loyalty(
        User.objects.filter(role=User.Role.CUSTOMER)
        .select_related("ambassador_profile")
        .annotate(
            ambassador_successful_count=Count(
                "ambassador_profile__referrals",
                filter=Q(ambassador_profile__referrals__status=Referral.Status.AWARDED),
            ),
            ambassador_pending_count=Count(
                "ambassador_profile__referrals",
                filter=Q(ambassador_profile__referrals__status=Referral.Status.PENDING),
            ),
        )
    ).order_by("-created_at")
    if q:
        queryset = queryset.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(phone_e164__icontains=q)
        )
    page_obj, pagination_query = _paginate(request, queryset, 25)
    for customer in page_obj.object_list:
        customer.loyalty_label = loyalty_label_from_count(
            customer.eligible_order_count,
            request.LANGUAGE_CODE,
        )
    return render(
        request,
        "management/customers.html",
        {
            "customers": page_obj.object_list,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
            "q": q,
            "result_count": page_obj.paginator.count,
            **page_copy(
                request,
                "العملاء",
                "Customers",
                "عرض بيانات العملاء الضرورية لخدمة الطلبات فقط.",
                "View only customer information required for order support.",
            ),
        },
    )


@staff_required
def supervisors(request):
    require_owner(request.user)
    q = _clean_search(request)
    queryset = (
        User.objects.filter(role=User.Role.SUPERVISOR)
        .select_related("supervisor_permissions")
        .order_by("-created_at")
    )
    if q:
        queryset = queryset.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )
    page_obj, pagination_query = _paginate(request, queryset, 24)
    return render(
        request,
        "management/supervisors.html",
        {
            "supervisors": page_obj.object_list,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
            "q": q,
            "result_count": page_obj.paginator.count,
            **page_copy(
                request,
                "المشرفون والصلاحيات",
                "Supervisors & Permissions",
                "إدارة حسابات المشرفين ومنح أقل صلاحية مطلوبة لكل مهمة.",
                "Manage supervisor accounts using least-privilege access.",
            ),
        },
    )


@staff_required
def supervisor_create(request):
    require_owner(request.user)
    form = SupervisorCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()

        # Security: newly provisioned supervisors start with zero application
        # permissions. Access is granted only on the separate permissions page.
        SupervisorPermission.objects.get_or_create(
            user=user,
            defaults={
                "view_products": False,
                "view_inventory": False,
                "view_orders": False,
            },
        )
        audit(
            request,
            "supervisor_created",
            user,
            new={
                "username": user.username,
                "country": user.country,
                "permissions": "none",
            },
        )
        return redirect(
            "core:management_supervisor_permissions",
            public_id=user.public_id,
        )

    return render(
        request,
        "management/supervisor_create.html",
        {
            "form": form,
            "title": "Create Supervisor"
            if request.LANGUAGE_CODE == "en"
            else "إنشاء حساب مشرف",
            "page_description": (
                "Create the supervisor account first. Permissions are granted separately in the next step."
                if request.LANGUAGE_CODE == "en"
                else "أنشئ حساب المشرف أولًا، ثم امنحه الصلاحيات بشكل منفصل في الخطوة التالية."
            ),
        },
    )


@staff_required
def supervisor_permissions(request, public_id):
    require_owner(request.user)
    user = get_object_or_404(User, public_id=public_id, role=User.Role.SUPERVISOR)
    permissions, _ = SupervisorPermission.objects.get_or_create(user=user)
    form = SupervisorPermissionForm(request.POST or None, instance=permissions)
    if request.method == "POST" and form.is_valid():
        before = {
            field.name: getattr(permissions, field.name)
            for field in permissions._meta.fields
            if field.name not in {"id", "user", "updated_at"}
        }
        updated_permissions = form.save()
        after = {
            field.name: getattr(updated_permissions, field.name)
            for field in updated_permissions._meta.fields
            if field.name not in {"id", "user", "updated_at"}
        }
        audit(
            request,
            "supervisor_permissions_changed",
            user,
            old=before,
            new=after,
        )
        return redirect("core:management_supervisors")
    return render(
        request,
        "management/supervisor_permissions.html",
        {
            "form": form,
            "supervisor": user,
            "title": f"Permissions — {user.username}"
            if request.LANGUAGE_CODE == "en"
            else f"صلاحيات {user.username}",
            "page_description": (
                "Grant only the minimum access this supervisor needs."
                if request.LANGUAGE_CODE == "en"
                else "امنح المشرف أقل قدر من الصلاحيات التي يحتاجها فقط."
            ),
        },
    )


@staff_required
def audit_logs(request):
    require_owner(request.user)

    q = _clean_search(request, 120)
    view_mode = (request.GET.get("view") or "audit").strip().lower()
    if view_mode not in {"audit", "security"}:
        view_mode = "audit"

    category = (request.GET.get("category") or "").strip()[:40]
    actor_role = (request.GET.get("actor_role") or "").strip()[:20]
    outcome = (request.GET.get("outcome") or "").strip()[:16]
    source = (request.GET.get("source") or "").strip()[:20]

    now = timezone.now()
    last_24h = now - timezone.timedelta(hours=24)

    audit_stats = {
        "total": AuditLog.objects.count(),
        "last_24h": AuditLog.objects.filter(created_at__gte=last_24h).count(),
        "failures": AuditLog.objects.filter(outcome=AuditLog.Outcome.FAILURE).count(),
        "security_events": SecurityEvent.objects.count(),
    }

    if view_mode == "security":
        queryset = SecurityEvent.objects.select_related("user").order_by("-created_at")
        if q:
            queryset = queryset.filter(
                Q(event__icontains=q)
                | Q(user__username__icontains=q)
                | Q(ip_address__icontains=q)
            )
        page_obj, pagination_query = _paginate(request, queryset, 40)
        logs = []
        security_events = page_obj.object_list
    else:
        queryset = AuditLog.objects.select_related("actor").order_by("-created_at")
        if q:
            queryset = queryset.filter(
                Q(action__icontains=q)
                | Q(category__icontains=q)
                | Q(object_type__icontains=q)
                | Q(object_reference__icontains=q)
                | Q(actor_username__icontains=q)
                | Q(request_id__icontains=q)
            )
        if category:
            queryset = queryset.filter(category=category)
        if actor_role:
            queryset = queryset.filter(actor_role=actor_role)
        if outcome:
            queryset = queryset.filter(outcome=outcome)
        if source:
            queryset = queryset.filter(source=source)

        page_obj, pagination_query = _paginate(request, queryset, 40)
        logs = page_obj.object_list
        security_events = []

    return render(
        request,
        "management/audit_logs.html",
        {
            "logs": logs,
            "security_events": security_events,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
            "q": q,
            "view_mode": view_mode,
            "category": category,
            "actor_role": actor_role,
            "outcome": outcome,
            "source": source,
            "audit_stats": audit_stats,
            "audit_categories": AuditLog.objects.exclude(category="")
            .values_list("category", flat=True)
            .distinct()
            .order_by("category"),
            "result_count": page_obj.paginator.count,
            **page_copy(
                request,
                "مركز التدقيق والأمان",
                "Audit & Security Center",
                "سجل مركزي غير قابل للتعديل للعمليات الحساسة وأحداث الأمان، متاح للمالك فقط.",
                "Owner-only, read-only center for sensitive business activity and security events.",
            ),
        },
    )


@staff_required
def audit_log_detail(request, pk):
    require_owner(request.user)
    log = get_object_or_404(AuditLog.objects.select_related("actor"), pk=pk)
    return render(
        request,
        "management/audit_log_detail.html",
        {
            "log": log,
            "integrity_valid": verify_integrity(log),
            **page_copy(
                request,
                "تفاصيل سجل التدقيق",
                "Audit Record Details",
                "تفاصيل العملية كما سجّلها النظام من جهة السيرفر.",
                "Server-recorded details for this immutable audit event.",
            ),
        },
    )


@staff_required
def abandoned_carts(request):
    require_permission(request.user, "view_abandoned_carts")
    threshold = timezone.now() - timezone.timedelta(
        minutes=settings.ABANDONED_CART_MINUTES
    )
    q = _clean_search(request)
    queryset = (
        Cart.objects.filter(
            converted_at__isnull=True, updated_at__lte=threshold, items__isnull=False
        )
        .select_related("user")
        .annotate(item_count=Count("items"))
        .order_by("-updated_at")
    )
    if q:
        queryset = queryset.filter(
            Q(contact_phone__icontains=q)
            | Q(user__username__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
        )
    page_obj, pagination_query = _paginate(request, queryset, 25)
    return render(
        request,
        "management/abandoned_carts.html",
        {
            "carts": page_obj.object_list,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
            "q": q,
            "result_count": page_obj.paginator.count,
            **page_copy(
                request,
                "السلات غير المكتملة",
                "Incomplete Carts",
                f"السلات التي لم يكتمل طلبها بعد {settings.ABANDONED_CART_MINUTES} دقيقة من آخر نشاط.",
                f"Carts not completed after {settings.ABANDONED_CART_MINUTES} minutes of inactivity.",
            ),
        },
    )


@staff_required
def management_search(request):
    q = _clean_search(request)
    product_results = []
    order_results = []
    customer_results = []
    if q:
        if can(request.user, "view_products"):
            product_results = Product.objects.filter(
                Q(product_reference__icontains=q)
                | Q(sku__icontains=q)
                | Q(name_ar__icontains=q)
                | Q(name_en__icontains=q)
            ).only(
                "public_id", "product_reference", "sku", "name_ar", "name_en", "status"
            )[:12]
        if can(request.user, "view_orders"):
            order_results = Order.objects.filter(
                Q(reference__icontains=q)
                | Q(customer_name__icontains=q)
                | Q(customer_phone__icontains=q)
            ).only("public_id", "reference", "customer_name", "status", "created_at")[
                :12
            ]
        if can(request.user, "view_customers"):
            customer_results = (
                User.objects.filter(role=User.Role.CUSTOMER)
                .filter(
                    Q(username__icontains=q)
                    | Q(first_name__icontains=q)
                    | Q(last_name__icontains=q)
                    | Q(email__icontains=q)
                    | Q(phone_e164__icontains=q)
                )
                .only(
                    "public_id",
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "phone_e164",
                )[:12]
            )
    return render(
        request,
        "management/search.html",
        {
            "q": q,
            "product_results": product_results,
            "order_results": order_results,
            "customer_results": customer_results,
            **page_copy(
                request,
                "البحث الإداري",
                "Management Search",
                "بحث موحد ضمن البيانات التي تسمح بها صلاحيات حسابك فقط.",
                "Search only the management data permitted by your assigned access.",
            ),
        },
    )


@staff_required
def promotions(request):
    require_owner(request.user)
    q = _clean_search(request)
    now = timezone.now()

    base_queryset = Promotion.objects.all()
    promotion_stats = base_queryset.aggregate(
        total=Count("pk"),
        active=Count(
            "pk", filter=Q(is_active=True, starts_at__lte=now, ends_at__gte=now)
        ),
        scheduled=Count("pk", filter=Q(is_active=True, starts_at__gt=now)),
        expired=Count("pk", filter=Q(ends_at__lt=now)),
    )

    queryset = base_queryset.prefetch_related("products", "categories").order_by(
        "-is_active", "priority", "-created_at"
    )
    if q:
        queryset = queryset.filter(Q(name_ar__icontains=q) | Q(name_en__icontains=q))

    page_obj, pagination_query = _paginate(request, queryset, 25)
    return render(
        request,
        "management/promotions.html",
        {
            "promotions": page_obj.object_list,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
            "q": q,
            "now": now,
            "promotion_stats": promotion_stats,
            **page_copy(
                request,
                "العروض والخصومات",
                "Promotions & Discounts",
                "إنشاء عروض آمنة على كل المنتجات أو تصنيفات أو منتجات محددة، مع هدية اختيارية.",
                "Create secure store-wide, category or product promotions with optional gifts.",
            ),
        },
    )


@staff_required
def promotion_create(request):
    require_owner(request.user)
    form = PromotionManagementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.updated_by = request.user
            obj.full_clean(exclude=["products", "categories"])
            obj.save()
            form.save_m2m()
        audit(
            request,
            "promotion_created",
            obj,
            new={
                "name_ar": obj.name_ar,
                "scope": obj.scope,
                "discount_type": obj.discount_type,
                "discount_value": str(obj.discount_value),
                "is_active": obj.is_active,
            },
        )
        return redirect(MANAGEMENT_PROMOTIONS_URL)
    return render(
        request,
        "management/promotion_form.html",
        {
            "form": form,
            "title": "Create Promotion"
            if request.LANGUAGE_CODE == "en"
            else "إنشاء عرض",
            "is_create": True,
        },
    )


@staff_required
def promotion_edit(request, public_id):
    require_owner(request.user)
    obj = get_object_or_404(Promotion, public_id=public_id)
    form = PromotionManagementForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        old = {
            "name_ar": obj.name_ar,
            "is_active": obj.is_active,
            "discount_value": str(obj.discount_value),
        }
        with transaction.atomic():
            updated = form.save(commit=False)
            updated.updated_by = request.user
            updated.full_clean(exclude=["products", "categories"])
            updated.save()
            form.save_m2m()
        audit(
            request,
            "promotion_updated",
            updated,
            old=old,
            new={
                "name_ar": updated.name_ar,
                "is_active": updated.is_active,
                "discount_value": str(updated.discount_value),
            },
        )
        return redirect(MANAGEMENT_PROMOTIONS_URL)
    return render(
        request,
        "management/promotion_form.html",
        {
            "form": form,
            "promotion": obj,
            "title": "Edit Promotion"
            if request.LANGUAGE_CODE == "en"
            else "تعديل العرض",
            "is_create": False,
        },
    )


@staff_required
@require_POST
def promotion_toggle(request, public_id):
    require_owner(request.user)
    obj = get_object_or_404(Promotion, public_id=public_id)
    old = obj.is_active
    obj.is_active = not obj.is_active
    obj.updated_by = request.user
    obj.save(update_fields=["is_active", "updated_by", "updated_at"])
    audit(
        request,
        "promotion_status_changed",
        obj,
        old={"is_active": old},
        new={"is_active": obj.is_active},
    )
    return redirect(MANAGEMENT_PROMOTIONS_URL)


@staff_required
def reservation_overrides(request):
    from django.contrib.auth import get_user_model

    from accounts.services.permission_service import require_owner
    from core.forms import ReservationOverrideForm

    require_owner(request.user)
    now = timezone.now()
    max_cap = max(
        4, min(int(getattr(settings, "CHECKOUT_RESERVATION_OVERRIDE_MAX", 10)), 20)
    )

    # Review customer-submitted requests. Never trust a requested limit from the browser;
    # the persisted request is re-read and capped server-side.
    if request.method == "POST" and request.POST.get("request_id"):
        action = (request.POST.get("request_action") or "").strip().lower()
        with transaction.atomic():
            req = get_object_or_404(
                ReservationLimitRequest.objects.select_for_update().select_related(
                    "user"
                ),
                pk=request.POST.get("request_id"),
            )
            if req.status != ReservationLimitRequest.Status.PENDING:
                messages.info(request, "تمت معالجة هذا الطلب مسبقًا.")
                return redirect(MANAGEMENT_RESERVATION_OVERRIDES_URL)
            if action == "approve":
                requested = min(max(4, req.requested_items), max_cap)
                ReservationLimitOverride.objects.filter(
                    user=req.user, expires_at__gt=now
                ).delete()
                override = ReservationLimitOverride.objects.create(
                    user=req.user,
                    max_items=requested,
                    expires_at=now + timezone.timedelta(minutes=15),
                    granted_by=request.user,
                    reason="Approved customer reservation limit request",
                )
                req.status = ReservationLimitRequest.Status.APPROVED
                req.reviewed_by = request.user
                req.reviewed_at = now
                req.save(
                    update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"]
                )
                audit(
                    request,
                    "reservation_limit_request_approved",
                    req,
                    new={
                        "customer": req.user.username,
                        "max_items": requested,
                        "expires_at": override.expires_at,
                    },
                )
                messages.success(
                    request,
                    f"تمت الموافقة على رفع الحد إلى {requested} قطع لمدة 15 دقيقة.",
                )
            elif action == "reject":
                req.status = ReservationLimitRequest.Status.REJECTED
                req.reviewed_by = request.user
                req.reviewed_at = now
                req.save(
                    update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"]
                )
                audit(
                    request,
                    "reservation_limit_request_rejected",
                    req,
                    new={
                        "customer": req.user.username,
                        "requested_items": req.requested_items,
                    },
                )
                messages.success(request, "تم رفض طلب رفع الحد.")
            else:
                messages.error(request, "إجراء غير صالح.")
        return redirect(MANAGEMENT_RESERVATION_OVERRIDES_URL)

    form = ReservationOverrideForm(request.POST or None)
    if (
        request.method == "POST"
        and not request.POST.get("request_id")
        and form.is_valid()
    ):
        user_model = get_user_model()
        ident = form.cleaned_data["customer"].strip()
        customer = user_model.objects.filter(
            Q(email__iexact=ident) | Q(username__iexact=ident), role="CUSTOMER"
        ).first()
        if not customer:
            form.add_error("customer", "لم يتم العثور على عميل مسجل بهذه البيانات.")
        else:
            requested = min(form.cleaned_data["max_items"], max_cap)
            ReservationLimitOverride.objects.filter(
                user=customer, expires_at__gt=now
            ).delete()
            override = ReservationLimitOverride.objects.create(
                user=customer,
                max_items=requested,
                expires_at=now + timezone.timedelta(minutes=15),
                granted_by=request.user,
                reason=form.cleaned_data.get("reason", ""),
            )
            audit(
                request,
                "reservation_override_granted",
                override,
                new={
                    "customer": customer.username,
                    "max_items": requested,
                    "expires_at": override.expires_at,
                },
            )
            messages.success(request, "تم منح العميل حد حجز مؤقت لمدة 15 دقيقة.")
            return redirect(MANAGEMENT_RESERVATION_OVERRIDES_URL)

    # Mark stale pending requests as expired to keep the owner queue useful.
    ReservationLimitRequest.objects.filter(
        status=ReservationLimitRequest.Status.PENDING,
        created_at__lt=now - timezone.timedelta(hours=24),
    ).update(status=ReservationLimitRequest.Status.EXPIRED, reviewed_at=now)
    pending_requests = (
        ReservationLimitRequest.objects.filter(
            status=ReservationLimitRequest.Status.PENDING
        )
        .select_related("user")
        .order_by("created_at")
    )
    active = (
        ReservationLimitOverride.objects.filter(expires_at__gt=now)
        .select_related("user", "granted_by")
        .order_by("expires_at")
    )
    return render(
        request,
        "management/reservation_overrides.html",
        {
            "form": form,
            "active_overrides": active,
            "pending_requests": pending_requests,
            "max_override_cap": max_cap,
            **page_copy(
                request,
                "طلبات واستثناءات الحجز",
                "Reservation Requests & Overrides",
                "مراجعة طلبات العملاء ورفع الحد مؤقتًا للعملاء الموثوقين فقط.",
                "Review customer requests and temporarily increase checkout limits for verified customers only.",
            ),
        },
    )


@staff_required
def receivables(request):
    require_owner(request.user)
    today=timezone.localdate()
    qs=Order.objects.filter(sale_channel=Order.SaleChannel.DIRECT, payment_status__in=[Order.PaymentStatus.UNPAID,Order.PaymentStatus.PARTIALLY_PAID], payment_due_date__isnull=False).prefetch_related("direct_payments").order_by("payment_due_date")
    rows=[]
    for order in qs:
        paid=order.direct_payments.aggregate(v=Sum("amount"))["v"] or 0
        outstanding=max(order.grand_total-paid,0)
        remind_on=order.payment_due_date-timedelta(days=order.payment_reminder_days)
        rows.append({"order":order,"paid":paid,"outstanding":outstanding,"overdue":order.payment_due_date<today,"due_soon":remind_on<=today<=order.payment_due_date})
    return render(request,"management/receivables.html",{"rows":rows,**page_copy(request,"الدفعات المستحقة","Receivables")})


@staff_required
def receivable_payment(request, public_id):
    require_owner(request.user)
    order = get_object_or_404(
        Order,
        public_id=public_id,
        sale_channel=Order.SaleChannel.DIRECT,
        payment_method=Order.PaymentMethod.DEFERRED,
    )
    paid = order.direct_payments.aggregate(v=Sum("amount"))["v"] or Decimal("0.00")
    outstanding = max(order.grand_total - paid, Decimal("0.00"))
    if outstanding <= 0 or order.payment_status == Order.PaymentStatus.PAID:
        messages.info(
            request,
            "تم سداد هذا البيع بالكامل."
            if request.LANGUAGE_CODE != "en"
            else "This sale is already paid in full.",
        )
        return redirect(MANAGEMENT_ORDER_URL, public_id=order.public_id)

    form = DirectPaymentEntryForm(
        request.POST or None,
        language_code=request.LANGUAGE_CODE,
        outstanding=outstanding,
    )
    if request.method == "POST" and form.is_valid():
        amount = form.cleaned_data["amount"]
        with transaction.atomic():
            locked = Order.objects.select_for_update().get(
                pk=order.pk,
                sale_channel=Order.SaleChannel.DIRECT,
                payment_method=Order.PaymentMethod.DEFERRED,
            )
            if locked.status in {Order.Status.CANCELLED, Order.Status.RETURNED}:
                raise PermissionDenied("Cancelled or returned sales cannot receive payments.")
            paid_locked = (
                locked.direct_payments.aggregate(v=Sum("amount"))["v"]
                or Decimal("0.00")
            )
            remaining = max(locked.grand_total - paid_locked, Decimal("0.00"))
            if amount > remaining:
                form.add_error(
                    "amount",
                    "تم تحديث الرصيد؛ أعد المحاولة."
                    if request.LANGUAGE_CODE != "en"
                    else "The balance changed; please try again.",
                )
            else:
                DirectPaymentEntry.objects.create(
                    order=locked,
                    amount=amount,
                    payment_method=form.cleaned_data["payment_method"],
                    note=(form.cleaned_data.get("note") or "")[:300],
                    received_by=request.user,
                )
                new_remaining = remaining - amount
                locked.payment_status = (
                    Order.PaymentStatus.PAID
                    if new_remaining == 0
                    else Order.PaymentStatus.PARTIALLY_PAID
                )
                update_fields = ["payment_status", "updated_at"]
                if new_remaining == 0:
                    locked.manual_paid_at = timezone.now()
                    locked.manual_paid_by = request.user
                    update_fields.extend(["manual_paid_at", "manual_paid_by"])
                locked.save(update_fields=update_fields)
                OrderTimelineEvent.objects.create(
                    order=locked,
                    kind=OrderTimelineEvent.Kind.PAYMENT_CHANGED,
                    label_ar="تم تسجيل دفعة على البيع المؤجل",
                    label_en="Deferred-sale payment recorded",
                    actor=request.user,
                    from_value=str(remaining),
                    to_value=str(new_remaining),
                )
                audit(
                    request,
                    "direct_receivable_payment_recorded",
                    locked,
                    new={
                        "amount": str(amount),
                        "remaining": str(new_remaining),
                        "payment_method": form.cleaned_data["payment_method"],
                    },
                )
                messages.success(
                    request,
                    (
                        f"تم تسجيل دفعة {amount:.2f} AED. المتبقي {new_remaining:.2f} AED."
                        if request.LANGUAGE_CODE != "en"
                        else f"Payment of {amount:.2f} AED recorded. Remaining: {new_remaining:.2f} AED."
                    ),
                )
                return redirect(
                    "core:management_receivable_payment",
                    public_id=locked.public_id,
                )

    return render(
        request,
        "management/receivable_payment.html",
        {
            "order": order,
            "form": form,
            "paid": paid,
            "outstanding": outstanding,
            "customer_display": (
                "Direct Customer"
                if request.LANGUAGE_CODE == "en"
                else "عميل مباشر"
            )
            if order.customer_name == "Direct Customer"
            else order.customer_name,
            **page_copy(request, "تسجيل دفعة", "Record Payment"),
        },
    )



@staff_required
def invoice_settings(request):
    require_owner(request.user)
    store, _ = StoreSetting.objects.get_or_create(singleton=True)
    form = InvoiceIdentitySettingsForm(
        request.POST or None,
        request.FILES or None,
        instance=store,
        language_code=request.LANGUAGE_CODE,
    )
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            locked = StoreSetting.objects.select_for_update().get(pk=store.pk)
            old = {
                "invoice_business_name": locked.invoice_business_name,
                "invoice_language": locked.invoice_language,
                "invoice_stamp_mode": locked.invoice_stamp_mode,
                "invoice_logo_public_id": locked.invoice_logo_public_id,
                "invoice_stamp_public_id": locked.invoice_stamp_public_id,
            }
            for field in form.Meta.fields:
                setattr(locked, field, form.cleaned_data[field])

            if form.cleaned_data.get("remove_logo") and locked.invoice_logo_public_id:
                delete_master_data_image(locked.invoice_logo_public_id)
                locked.invoice_logo_url = ""
                locked.invoice_logo_public_id = ""
            if form.cleaned_data.get("remove_stamp") and locked.invoice_stamp_public_id:
                delete_master_data_image(locked.invoice_stamp_public_id)
                locked.invoice_stamp_url = ""
                locked.invoice_stamp_public_id = ""

            logo = form.cleaned_data.get("logo")
            if logo:
                result, _ = upload_master_data_image(
                    logo, kind="invoice-logo", public_id=locked.pk
                )
                previous = locked.invoice_logo_public_id
                locked.invoice_logo_url = result.get("secure_url", "")
                locked.invoice_logo_public_id = result.get("public_id", "")
                if previous and previous != locked.invoice_logo_public_id:
                    delete_master_data_image(previous)

            stamp = form.cleaned_data.get("stamp")
            if stamp:
                result, _ = upload_master_data_image(
                    stamp, kind="invoice-stamp", public_id=locked.pk
                )
                previous = locked.invoice_stamp_public_id
                locked.invoice_stamp_url = result.get("secure_url", "")
                locked.invoice_stamp_public_id = result.get("public_id", "")
                if previous and previous != locked.invoice_stamp_public_id:
                    delete_master_data_image(previous)

            locked.save()
            audit(
                request,
                "invoice_settings_updated",
                locked,
                old=old,
                new={
                    "invoice_business_name": locked.invoice_business_name,
                    "invoice_language": locked.invoice_language,
                    "invoice_stamp_mode": locked.invoice_stamp_mode,
                    "invoice_logo_public_id": locked.invoice_logo_public_id,
                    "invoice_stamp_public_id": locked.invoice_stamp_public_id,
                },
            )
        messages.success(
            request,
            "تم تحديث إعدادات الفاتورة."
            if request.LANGUAGE_CODE != "en"
            else "Invoice settings updated.",
        )
        return redirect("core:management_invoice_settings")

    return render(
        request,
        "management/invoice_settings.html",
        {
            "form": form,
            "store_setting": store,
            **page_copy(request, "إعدادات الفاتورة", "Invoice Settings"),
        },
    )


@staff_required
@require_POST
def invoice_create(request, public_id):
    require_owner(request.user)
    order = get_object_or_404(Order, public_id=public_id)
    if order.status in {Order.Status.CANCELLED, Order.Status.RETURNED}:
        raise PermissionDenied("Cancelled or returned orders cannot be invoiced.")

    invoice, created = create_invoice_snapshot(order, request.user)
    if created:
        audit(
            request,
            "invoice_created",
            invoice,
            new={
                "invoice_number": invoice.invoice_number,
                "order_reference": invoice.order_reference_snapshot,
                "grand_total": str(invoice.grand_total_snapshot),
                "paid_total": str(invoice.paid_total_snapshot),
                "outstanding": str(invoice.outstanding_snapshot),
            },
        )
        messages.success(
            request,
            "تم إنشاء الفاتورة وحفظ نسخة مالية ثابتة."
            if request.LANGUAGE_CODE != "en"
            else "Invoice created as an immutable financial snapshot.",
        )
    return redirect("core:management_invoice", public_id=invoice.public_id)


@staff_required
@require_GET
def invoice_detail(request, public_id):
    require_permission(request.user, "view_orders")
    invoice = get_object_or_404(
        Invoice.objects.select_related("order", "issued_by").prefetch_related("items"),
        public_id=public_id,
    )
    return render(
        request,
        "management/invoice_detail.html",
        {
            "invoice": invoice,
            "invoice_setting": StoreSetting.objects.filter(singleton=True).first(),
            **page_copy(request, "الفاتورة", "Invoice"),
        },
    )


@staff_required
@require_GET
def invoice_pdf(request, public_id):
    require_permission(request.user, "view_orders")
    invoice = get_object_or_404(
        Invoice.objects.select_related("order", "issued_by").prefetch_related("items"),
        public_id=public_id,
    )
    pdf_bytes = render_invoice_pdf(invoice, StoreSetting.objects.filter(singleton=True).first())
    audit(
        request,
        "invoice_pdf_generated",
        invoice,
        new={"invoice_number": invoice.invoice_number},
    )
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{invoice.invoice_number}.pdf"'
    )
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


@staff_required
def product_custody(request, public_id):
    require_owner(request.user)
    product = get_object_or_404(Product, public_id=public_id)
    form = ProductCustodyForm(
        request.POST or None,
        initial={"placed_on": timezone.localdate()},
        language_code=request.LANGUAGE_CODE,
    )
    if request.method == "POST" and form.is_valid():
        entry = ProductCustodyHistory.objects.create(
            product=product,
            recorded_by=request.user,
            **form.cleaned_data,
        )
        audit(
            request,
            "product_custody_recorded",
            product,
            new={
                "location_name": entry.location_name,
                "holder_name": entry.holder_name,
                "placed_on": entry.placed_on.isoformat(),
                "note": entry.note,
            },
        )
        messages.success(
            request,
            "تم تسجيل موقع القطعة وحفظ الحركة في السجل."
            if request.LANGUAGE_CODE != "en"
            else "Product location recorded in the custody history.",
        )
        return redirect(
            "core:management_product_custody",
            public_id=product.public_id,
        )
    history = product.custody_history.select_related("recorded_by").order_by(
        "-placed_on", "-created_at"
    )
    return render(
        request,
        "management/product_custody.html",
        {
            "product": product,
            "form": form,
            "history": history,
            "current": history.first(),
            **page_copy(request, "مكان القطعة", "Product Location"),
        },
    )

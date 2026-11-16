import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from core.models import StoreSetting
from orders.models import Order, OrderNotification

DEFAULT_NOTIFICATION_EMAIL = 'info@haybatalsultan.com'
ORDER_NUMBER_AR = 'رقم الطلب'
ORDER_STATUS_AR = 'حالة الطلب'
MANAGEMENT_ORDER_URL = 'core:management_order'

logger = logging.getLogger("haybat.security")

BRAND_AR = "هيبة السلطان"
BRAND_EN = "Haybat Alsultan"


def _store_setting():
    return StoreSetting.objects.filter(singleton=True).first()


def _admin_email(store):
    return (
        getattr(store, "notification_email", "")
        or getattr(store, "email", "")
        or settings.STORE_CONTACT_EMAIL
    ).strip()


def _absolute(path):
    base = (getattr(settings, "PUBLIC_BASE_URL", "") or "").strip().rstrip("/")
    return f"{base}{path}" if base else path


def _brand_logo_url():
    return _absolute("/static/branding/logo-header.png")


def _reserve_notification(order, event_key, recipient_type, recipient):
    """Reserve one logical notification without breaking the surrounding transaction."""
    recipient = (recipient or "").strip().lower()
    if not recipient:
        return None
    marker, created = OrderNotification.objects.get_or_create(
        order=order,
        event_key=event_key[:80],
        recipient_type=recipient_type,
        recipient=recipient,
    )
    if not created:
        return None
    return marker


def _send(
    order,
    *,
    event_key,
    recipient_type,
    recipient,
    subject,
    title,
    intro,
    details,
    action_url="",
    action_label="",
    notice="",
    eyebrow="",
):
    marker = _reserve_notification(order, event_key, recipient_type, recipient)
    if marker is None:
        return False

    context = {
        "brand_ar": BRAND_AR,
        "brand_en": BRAND_EN,
        "brand_logo_url": _brand_logo_url(),
        "support_email": getattr(
            settings, "STORE_CONTACT_EMAIL", DEFAULT_NOTIFICATION_EMAIL
        ),
        "title": title,
        "eyebrow": eyebrow,
        "intro": intro,
        "order": order,
        "details": details,
        "action_url": action_url,
        "action_label": action_label,
        "notice": notice,
    }

    # Keep a useful text-only fallback for clients that block HTML.
    text_lines = [title, "", intro, ""]
    text_lines.extend(
        f"{label}: {value}" for label, value in details if value not in (None, "")
    )
    if action_url:
        text_lines.extend(["", f"{action_label}: {action_url}"])
    if notice:
        text_lines.extend(["", notice])
    text_lines.extend(
        [
            "",
            f"{BRAND_AR} — {BRAND_EN}",
            getattr(settings, "STORE_CONTACT_EMAIL", DEFAULT_NOTIFICATION_EMAIL),
        ]
    )
    body = "\n".join(text_lines)

    try:
        html_body = render_to_string("orders/emails/transactional.html", context)
        message = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)
        marker.sent = True
        marker.save(update_fields=["sent"])
        return True
    except Exception as exc:
        # Do not expose body, recipient, Stripe identifiers, tokens, or SMTP credentials in logs.
        logger.warning(
            "order_email_notification_failed event=%s exception_type=%s",
            event_key,
            type(exc).__name__,
        )
        marker.delete()
        return False


def _item_summary(order):
    codes = list(order.items.values_list("sku", flat=True)[:20])
    return ", ".join(codes) if codes else "—"


def _payment_method_label(order):
    return order.get_payment_method_display() or "—"


def _admin_details(order):
    return [
        (ORDER_NUMBER_AR, order.reference),
        ("العميل", order.customer_name or "—"),
        ("رقم التواصل", order.customer_phone or "—"),
        ("عدد القطع", str(order.items.count())),
        ("أرقام القطع", _item_summary(order)),
        ("إجمالي الطلب", f"{order.grand_total:.2f} {order.currency}"),
        ("طريقة الدفع", _payment_method_label(order)),
        ("حالة الدفع", order.get_payment_status_display()),
        (ORDER_STATUS_AR, order.get_status_display()),
    ]


def notify_order_created(order_id):
    order = Order.objects.prefetch_related("items").get(pk=order_id)
    store = _store_setting()
    if not store or not getattr(store, "notify_admin_new_order", True):
        return

    _send(
        order,
        event_key="admin:new_order",
        recipient_type=OrderNotification.RecipientType.ADMIN,
        recipient=_admin_email(store),
        subject=f"طلب جديد | {order.reference} | {BRAND_AR}",
        eyebrow="تنبيه طلب جديد",
        title="تم استلام طلب جديد",
        intro="تم إنشاء طلب جديد في متجر هيبة السلطان ويحتاج إلى المتابعة حسب طريقة الدفع وحالة الطلب.",
        details=_admin_details(order),
        action_url=_absolute(
            reverse(MANAGEMENT_ORDER_URL, kwargs={"public_id": order.public_id})
        ),
        action_label="فتح الطلب في بوابة الإدارة",
        notice="ملاحظة أمنية: لا تعتمد على بيانات البريد لتغيير حالة الدفع. حالة Stripe تُحدّث من النظام الموثوق فقط.",
    )


def notify_payment_received(order_id):
    order = Order.objects.prefetch_related("items").get(pk=order_id)
    store = _store_setting()

    if store and getattr(store, "notify_admin_payment", True):
        _send(
            order,
            event_key="admin:payment_received",
            recipient_type=OrderNotification.RecipientType.ADMIN,
            recipient=_admin_email(store),
            subject=f"تم استلام الدفعة | {order.reference} | {BRAND_AR}",
            eyebrow="تأكيد مالي",
            title="تم تأكيد استلام الدفعة",
            intro="تم تأكيد الدفع للطلب بنجاح. يمكن الآن متابعة التجهيز والتوصيل من بوابة الإدارة.",
            details=_admin_details(order),
            action_url=_absolute(
                reverse(MANAGEMENT_ORDER_URL, kwargs={"public_id": order.public_id})
            ),
            action_label="متابعة الطلب",
        )

    if order.customer_email and (
        not store or getattr(store, "notify_customer_payment", True)
    ):
        _send(
            order,
            event_key="customer:payment_received",
            recipient_type=OrderNotification.RecipientType.CUSTOMER,
            recipient=order.customer_email,
            subject=f"تم تأكيد طلبك {order.reference} | {BRAND_AR}",
            eyebrow="تأكيد الطلب",
            title="تم استلام دفعتك وتأكيد طلبك",
            intro="شكرًا لاختيارك هيبة السلطان. تم تأكيد دفعتك بنجاح، وسيبدأ تجهيز طلبك للمرحلة التالية.",
            details=[
                (ORDER_NUMBER_AR, order.reference),
                ("عدد القطع", str(order.items.count())),
                ("أرقام القطع", _item_summary(order)),
                ("إجمالي الطلب", f"{order.grand_total:.2f} {order.currency}"),
                (ORDER_STATUS_AR, order.get_status_display()),
            ],
            action_url=_absolute(
                reverse("orders:detail", kwargs={"public_id": order.public_id})
            ),
            action_label="عرض تفاصيل الطلب",
            notice="احتفظ برقم الطلب للرجوع إليه عند التواصل معنا.",
        )


def notify_order_status(order_id, status):
    order = Order.objects.prefetch_related("items").get(pk=order_id)
    store = _store_setting()

    customer_status = {
        Order.Status.SHIPPED: (
            "تم شحن طلبك",
            "تم تسليم طلبك لشركة التوصيل، ويمكنك متابعة تقدم الشحنة من خلال معلومات التتبع أدناه.",
        ),
        Order.Status.OUT_FOR_DELIVERY: (
            "طلبك خرج للتوصيل",
            "طلبك الآن مع فريق التوصيل وفي طريقه إليك. يرجى إبقاء رقم التواصل متاحًا لاستلام الشحنة.",
        ),
        Order.Status.DELIVERED: (
            "تم تسليم طلبك",
            "يسعدنا إبلاغك بأن طلبك تم تسليمه. شكرًا لثقتك واختيارك هيبة السلطان.",
        ),
    }

    if (
        order.customer_email
        and (not store or getattr(store, "notify_customer_shipping", True))
        and status in customer_status
    ):
        title, intro = customer_status[status]
        details = [
            (ORDER_NUMBER_AR, order.reference),
            (ORDER_STATUS_AR, order.get_status_display()),
        ]
        if order.shipping_carrier:
            details.append(("شركة التوصيل", order.shipping_carrier))
        if order.tracking_number:
            details.append(("رقم التتبع", order.tracking_number))

        action_url = order.tracking_url or _absolute(
            reverse("orders:detail", kwargs={"public_id": order.public_id})
        )
        action_label = "تتبع الشحنة" if order.tracking_url else "عرض تفاصيل الطلب"

        _send(
            order,
            event_key=f"customer:status:{status}",
            recipient_type=OrderNotification.RecipientType.CUSTOMER,
            recipient=order.customer_email,
            subject=f"{title} | {order.reference} | {BRAND_AR}",
            eyebrow="تحديث التوصيل",
            title=title,
            intro=intro,
            details=details,
            action_url=action_url,
            action_label=action_label,
            notice="إذا احتجت إلى مساعدة بشأن التسليم، تواصل معنا واذكر رقم الطلب.",
        )

    if (
        store
        and getattr(store, "notify_admin_shipping", False)
        and status
        in {
            Order.Status.SHIPPED,
            Order.Status.DELIVERED,
        }
    ):
        _send(
            order,
            event_key=f"admin:status:{status}",
            recipient_type=OrderNotification.RecipientType.ADMIN,
            recipient=_admin_email(store),
            subject=f"تحديث التوصيل | {order.reference} | {BRAND_AR}",
            eyebrow="تحديث تشغيلي",
            title=f"تم تحديث الطلب إلى: {order.get_status_display()}",
            intro="تم تسجيل تحديث جديد على مرحلة التوصيل لهذا الطلب.",
            details=_admin_details(order),
            action_url=_absolute(
                reverse(MANAGEMENT_ORDER_URL, kwargs={"public_id": order.public_id})
            ),
            action_label="فتح الطلب في بوابة الإدارة",
        )


def notify_reservation_limit_request(request_id):
    """Send one professional admin alert for a checkout limit request.

    This notification contains only operational data and never exposes cart/session
    identifiers, Stripe identifiers, secrets, or customer address data.
    """
    from orders.models import ReservationLimitRequest

    req = (
        ReservationLimitRequest.objects.select_related("user")
        .filter(pk=request_id)
        .first()
    )
    if not req or req.admin_notified_at:
        return False
    store = _store_setting()
    recipient = (
        _admin_email(store)
        if store
        else getattr(settings, "STORE_CONTACT_EMAIL", DEFAULT_NOTIFICATION_EMAIL)
    )
    if not recipient:
        return False
    dashboard_url = _absolute(reverse("core:management_reservation_overrides"))
    username = req.user.get_full_name() or req.user.username
    subject = f"طلب رفع حد الحجز | {req.requested_items} قطع | {BRAND_AR}"
    context = {
        "brand_ar": BRAND_AR,
        "brand_en": BRAND_EN,
        "brand_logo_url": _brand_logo_url(),
        "support_email": getattr(
            settings, "STORE_CONTACT_EMAIL", DEFAULT_NOTIFICATION_EMAIL
        ),
        "title": "طلب رفع حد الحجز",
        "eyebrow": "تنبيه تشغيلي",
        "intro": "طلب عميل مسجل رفع الحد المؤقت لإتمام الطلب. راجع الطلب من بوابة الإدارة قبل منح أي استثناء.",
        "details": [
            ("العميل", username),
            ("البريد", req.user.email or "—"),
            ("العدد المطلوب", str(req.requested_items)),
            ("الحالة", "بانتظار المراجعة"),
        ],
        "action_url": dashboard_url,
        "action_label": "مراجعة طلب رفع الحد",
        "notice": "للحماية من حجز المخزون، الاستثناء مؤقت لمدة 15 دقيقة ويُمنح من حساب المالك فقط.",
        "order": None,
    }
    text = (
        f"طلب رفع حد الحجز\n\nالعميل: {username}\nالبريد: {req.user.email or '—'}\n"
        f"العدد المطلوب: {req.requested_items}\n\nمراجعة الطلب: {dashboard_url}\n\n{BRAND_AR} — {BRAND_EN}"
    )
    try:
        html = render_to_string("orders/emails/transactional.html", context)
        message = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        message.attach_alternative(html, "text/html")
        message.send(fail_silently=False)
        from django.utils import timezone

        ReservationLimitRequest.objects.filter(
            pk=req.pk, admin_notified_at__isnull=True
        ).update(admin_notified_at=timezone.now())
        return True
    except Exception as exc:
        logger.warning(
            "reservation_limit_request_email_failed exception_type=%s",
            type(exc).__name__,
        )
        return False

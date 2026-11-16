from django import template

from orders.models import Order

register = template.Library()

_STATUS_AR = {
    Order.Status.PENDING: "بانتظار التأكيد",
    Order.Status.CONFIRMED: "تم تأكيد الطلب",
    Order.Status.PREPARING: "جاري التجهيز",
    Order.Status.READY: "جاهز للتوصيل",
    Order.Status.SHIPPED: "تم الشحن",
    Order.Status.OUT_FOR_DELIVERY: "خرج للتوصيل",
    Order.Status.DELIVERED: "تم التسليم",
    Order.Status.CANCELLED: "ملغي",
    Order.Status.RETURNED: "مرتجع",
}

_PAYMENT_AR = {
    Order.PaymentStatus.UNPAID: "بانتظار الدفع",
    Order.PaymentStatus.PENDING: "قيد الدفع",
    Order.PaymentStatus.PAID: "تم الدفع",
    Order.PaymentStatus.FAILED: "تعذر الدفع",
    Order.PaymentStatus.REFUNDED: "تم الاسترداد",
    Order.PaymentStatus.PARTIAL: "استرداد جزئي",
}

_STATUS_CLASS = {
    Order.Status.PENDING: "is-pending",
    Order.Status.CONFIRMED: "is-confirmed",
    Order.Status.PREPARING: "is-progress",
    Order.Status.READY: "is-progress",
    Order.Status.SHIPPED: "is-progress",
    Order.Status.OUT_FOR_DELIVERY: "is-progress",
    Order.Status.DELIVERED: "is-success",
    Order.Status.CANCELLED: "is-muted",
    Order.Status.RETURNED: "is-muted",
}

_PAYMENT_CLASS = {
    Order.PaymentStatus.PAID: "is-success",
    Order.PaymentStatus.UNPAID: "is-pending",
    Order.PaymentStatus.PENDING: "is-pending",
    Order.PaymentStatus.FAILED: "is-danger",
    Order.PaymentStatus.REFUNDED: "is-muted",
    Order.PaymentStatus.PARTIAL: "is-warning",
}


@register.filter
def order_status_label(order, language_code="ar"):
    if language_code == "en":
        return order.get_status_display()
    return _STATUS_AR.get(order.status, order.get_status_display())


@register.filter
def payment_status_label(order, language_code="ar"):
    if language_code == "en":
        return order.get_payment_status_display()
    return _PAYMENT_AR.get(order.payment_status, order.get_payment_status_display())


@register.filter
def order_status_class(order):
    return _STATUS_CLASS.get(order.status, "is-muted")


@register.filter
def payment_status_class(order):
    return _PAYMENT_CLASS.get(order.payment_status, "is-muted")

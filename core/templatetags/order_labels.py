from django import template
from django.utils.translation import get_language

register = template.Library()


def _arabic():
    return (get_language() or "").lower().startswith("ar")


@register.filter
def order_status_label(value):
    if not _arabic():
        return {
            "PENDING": "Pending Confirmation",
            "CONFIRMED": "Confirmed",
            "PREPARING": "Preparing",
            "READY": "Ready for Delivery",
            "SHIPPED": "Shipped",
            "OUT_FOR_DELIVERY": "Out for Delivery",
            "DELIVERED": "Delivered",
            "CANCELLED": "Cancelled",
            "RETURNED": "Returned",
        }.get(str(value), str(value or "—"))
    return {
        "PENDING": "بانتظار التأكيد",
        "CONFIRMED": "تم التأكيد",
        "PREPARING": "جاري التجهيز",
        "READY": "جاهز للتوصيل",
        "SHIPPED": "تم الشحن",
        "OUT_FOR_DELIVERY": "خرج للتوصيل",
        "DELIVERED": "تم التسليم",
        "CANCELLED": "ملغي",
        "RETURNED": "مرتجع",
    }.get(str(value), str(value or "—"))


@register.filter
def payment_status_label(value):
    if not _arabic():
        return {
            "UNPAID": "Unpaid",
            "PENDING": "Pending",
            "PAID": "Paid",
            "FAILED": "Failed",
            "REFUNDED": "Refunded",
            "PARTIAL": "Partially Refunded",
        }.get(str(value), str(value or "—"))
    return {
        "UNPAID": "غير مدفوع",
        "PENDING": "قيد الدفع",
        "PAID": "مدفوع",
        "FAILED": "فشل الدفع",
        "REFUNDED": "مسترد",
        "PARTIAL": "مسترد جزئيًا",
    }.get(str(value), str(value or "—"))


@register.filter
def payment_method_label(value):
    if str(value) == "STRIPE":
        return "Stripe"
    if str(value) == "MANUAL":
        return "Manual / WhatsApp" if not _arabic() else "تحويل يدوي / واتساب"
    return "Not selected" if not _arabic() else "لم يتم الاختيار"

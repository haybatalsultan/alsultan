from urllib.parse import urlencode

from django.conf import settings


def build_message(order):
    lines = [
        "New Order — Haybat Al Sultan",
        "",
        f"Order: {order.reference}",
        f"Customer: {order.customer_name}",
        f"Phone: {order.customer_phone}",
        "",
        "Products:",
    ]
    for i, item in enumerate(order.items.all(), 1):
        lines += [
            f"{i} × {item.quantity} {item.name_en or item.name_ar}",
            f"SKU: {item.sku}",
        ]
    lines += [
        "",
        f"Total: AED {order.grand_total}",
        f"Delivery: {order.emirate or order.country}",
        f"Order: {order.get_status_display()}",
        f"Payment: {order.get_payment_status_display()}",
    ]
    return "\n".join(lines)


def whatsapp_url(order):
    number = "".join(ch for ch in settings.WHATSAPP_NUMBER if ch.isdigit())
    if not number:
        return ""
    return f"https://wa.me/{number}?" + urlencode({"text": build_message(order)})

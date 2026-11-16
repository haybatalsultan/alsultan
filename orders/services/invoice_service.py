from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from orders.models import Invoice, InvoiceItem, Order


def _paid_total(order):
    if order.payment_method == Order.PaymentMethod.DEFERRED:
        return order.direct_payments.aggregate(v=Sum("amount"))["v"] or Decimal("0.00")
    if order.payment_status == Order.PaymentStatus.PAID:
        return order.grand_total
    return Decimal("0.00")


def build_invoice_number(order):
    year = (order.created_at or timezone.now()).year
    return f"INV-{year}-{order.pk:06d}"


def create_invoice_snapshot(order, issued_by):
    """Create exactly one immutable invoice snapshot for an order."""
    with transaction.atomic():
        locked = (
            Order.objects.select_for_update()
            .prefetch_related("items", "direct_payments")
            .get(pk=order.pk)
        )
        existing = Invoice.objects.filter(order=locked).first()
        if existing:
            return existing, False

        paid = _paid_total(locked)
        outstanding = max(locked.grand_total - paid, Decimal("0.00"))
        invoice = Invoice.objects.create(
            order=locked,
            invoice_number=build_invoice_number(locked),
            issued_by=issued_by,
            order_reference_snapshot=locked.reference,
            customer_name_snapshot=locked.customer_name or "",
            customer_phone_snapshot=locked.customer_phone or "",
            customer_email_snapshot=locked.customer_email or "",
            currency_snapshot=locked.currency,
            subtotal_snapshot=locked.subtotal,
            discount_total_snapshot=locked.discount_total,
            tax_total_snapshot=locked.tax_total,
            shipping_total_snapshot=locked.shipping_total,
            grand_total_snapshot=locked.grand_total,
            paid_total_snapshot=paid,
            outstanding_snapshot=outstanding,
            payment_status_snapshot=locked.payment_status,
            payment_method_snapshot=locked.payment_method,
            payment_due_date_snapshot=locked.payment_due_date,
            delivery_method_snapshot=locked.delivery_method,
            delivered_at_snapshot=locked.delivered_at,
        )

        InvoiceItem.objects.bulk_create(
            [
                InvoiceItem(
                    invoice=invoice,
                    product_reference_snapshot=item.product_reference,
                    sku_snapshot=item.sku,
                    name_ar_snapshot=item.name_ar,
                    name_en_snapshot=item.name_en,
                    quantity_snapshot=item.quantity,
                    unit_price_snapshot=item.unit_price,
                    discount_snapshot=item.discount,
                    tax_snapshot=item.tax,
                    line_total_snapshot=item.line_total,
                    original_bead_count_snapshot=item.original_bead_count_snapshot,
                    requested_bead_count_snapshot=item.requested_bead_count_snapshot,
                )
                for item in locked.items.all()
            ]
        )
        return invoice, True


def invoice_pdf_context(invoice, invoice_setting=None):
    """Presentation-only labels from immutable invoice snapshot values."""
    payment_method = {
        "CASH": "نقدي",
        "BANK_TRANSFER": "تحويل بنكي",
        "POS": "بطاقة / POS",
        "OTHER": "أخرى",
        "DEFERRED": "مؤجل",
        "UNSET": "مدفوع / مؤكد" if invoice.payment_status_snapshot == "PAID" else "غير محدد",
    }.get(invoice.payment_method_snapshot, "غير محدد")
    payment_status = {
        "PAID": "مدفوع",
        "PARTIALLY_PAID": "مدفوع جزئيًا",
        "UNPAID": "غير مدفوع",
        "FAILED": "فشل الدفع",
        "REFUNDED": "مسترد",
    }.get(invoice.payment_status_snapshot, "غير مدفوع")
    delivery = "استلام يدًا بيد" if invoice.delivery_method_snapshot == "HAND_TO_HAND" else "توصيل"

    if invoice.payment_status_snapshot == "PAID":
        status_text = "✓ مدفوع"
    elif invoice.payment_status_snapshot == "PARTIALLY_PAID":
        status_text = f"مدفوع جزئيًا · المتبقي {invoice.outstanding_snapshot:,.2f} {invoice.currency_snapshot}"
    elif invoice.payment_method_snapshot == "DEFERRED":
        status_text = "مؤجل"
        if invoice.payment_due_date_snapshot:
            status_text += f" · مستحق {invoice.payment_due_date_snapshot.strftime('%d/%m/%Y')}"
    else:
        status_text = "غير مدفوع"

    customer = invoice.customer_name_snapshot or "عميل مباشر"
    if customer == "Direct Customer":
        customer = "عميل مباشر"

    stamp_mode = getattr(invoice_setting, "invoice_stamp_mode", "PAID")
    show_stamp = stamp_mode == "ALWAYS" or (
        stamp_mode == "PAID" and invoice.payment_status_snapshot == "PAID"
    )
    return {
        "invoice": invoice,
        "invoice_setting": invoice_setting,
        "customer_display": customer,
        "payment_method_display": payment_method,
        "payment_status_display": payment_status,
        "delivery_display": delivery,
        "status_text": status_text,
        "show_stamp": show_stamp,
    }


def _trusted_brand_image_bytes(url, max_bytes=2_500_000):
    """Fetch configured branding only from HTTPS Cloudinary and verify it as an image."""
    if not url:
        return None
    from io import BytesIO as _BytesIO
    from urllib.parse import urlparse
    from urllib.request import Request, urlopen

    from PIL import Image as PILImage

    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "res.cloudinary.com":
        return None
    try:
        request = Request(url, headers={"User-Agent": "HaybatInvoice/2.1"})
        with urlopen(request, timeout=4) as response:
            if response.status != 200:
                return None
            content_type = (response.headers.get("Content-Type") or "").lower()
            if content_type not in {"image/png", "image/jpeg", "image/webp"}:
                return None
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes:
                return None
        with PILImage.open(_BytesIO(data)) as image:
            image.verify()
        return data, content_type
    except Exception:
        return None


def _brand_data_uri(url):
    import base64

    result = _trusted_brand_image_bytes(url)
    if not result:
        return ""
    data, content_type = result
    return f"data:{content_type};base64,{base64.b64encode(data).decode('ascii')}"


def _default_logo_data_uri():
    """Embed the project's existing logo so Chromium never needs a remote logo request."""
    import base64
    from django.conf import settings as django_settings

    path = Path(django_settings.BASE_DIR) / "static" / "branding" / "logo-header.png"
    if not path.exists():
        return ""
    data = path.read_bytes()
    if len(data) > 2_500_000:
        return ""
    return f"data:image/png;base64,{base64.b64encode(data).decode('ascii')}"

def render_invoice_pdf(invoice, invoice_setting=None):
    """Render the trusted Arabic invoice template in headless Chromium."""
    from django.template.loader import render_to_string
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    context = invoice_pdf_context(invoice, invoice_setting)
    context["logo_data_uri"] = (
        _brand_data_uri(getattr(invoice_setting, "invoice_logo_url", ""))
        or _default_logo_data_uri()
    )
    context["stamp_data_uri"] = (
        _brand_data_uri(getattr(invoice_setting, "invoice_stamp_url", ""))
        if context["show_stamp"]
        else ""
    )
    html = render_to_string("management/invoice_pdf_browser.html", context)

    browser = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox"],
            )
            page = browser.new_page(
                viewport={"width": 1240, "height": 1754},
                locale="ar-AE",
            )
            # Allow only the trusted Cairo font CDN. Branding is embedded as data URIs.
            def _route(request_route):
                from urllib.parse import urlparse

                url = request_route.request.url
                if url.startswith(("data:", "about:")):
                    return request_route.continue_()
                host = urlparse(url).hostname or ""
                if host in {"fonts.googleapis.com", "fonts.gstatic.com"}:
                    return request_route.continue_()
                return request_route.abort()

            page.route("**/*", _route)
            page.set_content(html, wait_until="networkidle", timeout=15_000)
            page.evaluate("document.fonts.ready")
            page.emulate_media(media="print")
            pdf = page.pdf(
                format="A4",
                print_background=True,
                margin={
                    "top": "10mm",
                    "right": "10mm",
                    "bottom": "10mm",
                    "left": "10mm",
                },
                prefer_css_page_size=True,
            )
            return pdf
    except PlaywrightError as exc:
        raise RuntimeError(
            "Chromium PDF renderer is unavailable. Run: python -m playwright install chromium"
        ) from exc
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass

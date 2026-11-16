from pathlib import Path

from django.test import SimpleTestCase


class ArabicInvoiceLayoutV20821Fix2Tests(SimpleTestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_management_dashboard_exposes_owner_invoice_settings_card(self):
        template = (self.root / "templates/management/dashboard.html").read_text(encoding="utf-8")
        self.assertIn("invoice-settings-tool", template)
        self.assertIn("management_invoice_settings", template)
        self.assertIn("إعدادات الفاتورة", template)

    def test_invoice_preview_is_arabic_first_rtl(self):
        template = (self.root / "templates/management/invoice_detail.html").read_text(encoding="utf-8")
        self.assertIn('class="haybat-invoice modern-arabic-invoice" dir="rtl"', template)
        for label in ("رقم القطعة", "البيان", "الكمية", "سعر الوحدة", "الدفع والتسليم", "ملخص الفاتورة"):
            self.assertIn(label, template)
        # HAND_TO_HAND is a legitimate internal enum used by the Django template
        # to choose the localized customer-facing label. The invariant is that
        # the Arabic label exists; rendered-response tests cover raw-code leakage.
        self.assertIn("استلام يدًا بيد", template)

    def test_pdf_uses_browser_rendered_arabic_rtl_template(self):
        service=(self.root/"orders/services/invoice_service.py").read_text(encoding="utf-8")
        template=(self.root/"templates/management/invoice_pdf_browser.html").read_text(encoding="utf-8")
        self.assertIn("management/invoice_pdf_browser.html", service)
        self.assertIn('lang="ar" dir="rtl"', template)
        self.assertIn("الدفع والتسليم", template)
        self.assertIn("ملخص الفاتورة", template)

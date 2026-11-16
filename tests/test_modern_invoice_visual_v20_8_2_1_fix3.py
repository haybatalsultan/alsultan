from pathlib import Path
from django.test import SimpleTestCase


class ModernInvoiceVisualV20821Fix3Tests(SimpleTestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_preview_uses_modern_compact_arabic_layout(self):
        template = (self.root / "templates/management/invoice_detail.html").read_text(encoding="utf-8")
        for token in (
            "modern-arabic-invoice",
            "modern-invoice-header",
            "modern-status-badge",
            "modern-invoice-meta",
            "modern-invoice-table",
            "modern-invoice-finance",
            "modern-invoice-footer",
        ):
            self.assertIn(token, template)
        self.assertIn("عميل مباشر", template)
        self.assertIn("استلام يدًا بيد", template)

    def test_pdf_uses_shared_modern_html_visual_hierarchy(self):
        service = (self.root / "orders/services/invoice_service.py").read_text(encoding="utf-8")
        template = (self.root / "templates/management/invoice_pdf_browser.html").read_text(encoding="utf-8")
        self.assertIn("invoice_pdf_context", service)
        self.assertIn('customer == "Direct Customer"', service)
        self.assertIn("✓ مدفوع", service)
        for label in ("الدفع والتسليم", "ملخص الفاتورة", "رقم القطعة"):
            self.assertIn(label, template)

    def test_visual_polish_does_not_add_financial_edit_fields(self):
        template = (self.root / "templates/management/invoice_detail.html").read_text(encoding="utf-8")
        for forbidden in ('name="grand_total', 'name="paid_total', 'name="outstanding'):
            self.assertNotIn(forbidden, template)

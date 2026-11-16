from pathlib import Path
from django.test import SimpleTestCase

class InvoiceDependencyV2082Fix1Tests(SimpleTestCase):
    def test_invoice_pdf_uses_browser_engine_without_rust_bidi(self):
        root=Path(__file__).resolve().parents[1]
        requirements=(root/"requirements.txt").read_text(encoding="utf-8").lower()
        service=(root/"orders/services/invoice_service.py").read_text(encoding="utf-8")
        self.assertNotIn("python-bidi", requirements)
        self.assertNotIn("xhtml2pdf", requirements)
        self.assertIn("playwright==1.55.0", requirements)
        self.assertIn("playwright.chromium.launch", service)

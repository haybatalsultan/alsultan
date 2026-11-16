from pathlib import Path
from django.test import SimpleTestCase

class BrowserPdfBrandingV20823Fix1Tests(SimpleTestCase):
    def setUp(self): self.root=Path(__file__).resolve().parents[1]
    def test_pdf_template_uses_cairo(self):
        template=(self.root/"templates/management/invoice_pdf_browser.html").read_text(encoding="utf-8")
        self.assertIn("family=Cairo",template)
        self.assertIn('font-family:"Cairo"',template)
    def test_logo_and_stamp_are_embedded_not_remote_in_template(self):
        service=(self.root/"orders/services/invoice_service.py").read_text(encoding="utf-8")
        template=(self.root/"templates/management/invoice_pdf_browser.html").read_text(encoding="utf-8")
        self.assertIn("_brand_data_uri",service)
        self.assertIn("_default_logo_data_uri",service)
        self.assertIn("logo_data_uri",template)
        self.assertIn("stamp_data_uri",template)
    def test_browser_waits_for_fonts_and_limits_network(self):
        service=(self.root/"orders/services/invoice_service.py").read_text(encoding="utf-8")
        self.assertIn("document.fonts.ready",service)
        self.assertIn('fonts.googleapis.com", "fonts.gstatic.com',service)
        self.assertIn("request_route.abort()",service)

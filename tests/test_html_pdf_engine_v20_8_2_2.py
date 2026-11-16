from pathlib import Path
from django.test import SimpleTestCase

class BrowserPdfEngineV20823Tests(SimpleTestCase):
    def setUp(self): self.root=Path(__file__).resolve().parents[1]
    def test_pdf_uses_trusted_browser_template(self):
        service=(self.root/"orders/services/invoice_service.py").read_text(encoding="utf-8")
        self.assertIn("sync_playwright",service)
        self.assertIn("page.set_content",service)
        self.assertIn("page.pdf",service)
    def test_template_is_arabic_rtl_and_script_free(self):
        template=(self.root/"templates/management/invoice_pdf_browser.html").read_text(encoding="utf-8")
        self.assertIn('lang="ar" dir="rtl"',template)
        self.assertNotIn("<script",template.lower())
    def test_brand_urls_are_cloudinary_https_only(self):
        service=(self.root/"orders/services/invoice_service.py").read_text(encoding="utf-8")
        self.assertIn('parsed.scheme != "https"',service)
        self.assertIn('parsed.hostname != "res.cloudinary.com"',service)

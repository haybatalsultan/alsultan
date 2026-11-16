from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

CANONICAL_PHONE = "+971504084006"
CANONICAL_DIGITS = "971504084006"
CANONICAL_DISPLAY = "+971 50 408 4006"


@override_settings(
    STORE_CONTACT_PHONE=CANONICAL_PHONE,
    WHATSAPP_NUMBER=CANONICAL_PHONE,
)
class CanonicalStoreContactTests(TestCase):
    def test_home_uses_canonical_phone_and_whatsapp(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, CANONICAL_DISPLAY)
        self.assertContains(response, f"tel:{CANONICAL_PHONE}")
        self.assertContains(response, f"https://wa.me/{CANONICAL_DIGITS}")

    def test_faq_uses_canonical_display_phone(self):
        response = self.client.get(reverse("core:info", args=["faq"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, CANONICAL_DISPLAY)

    def test_context_exposes_canonical_contact(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.context["STORE_CONTACT_PHONE"], CANONICAL_PHONE)
        self.assertEqual(
            response.context["STORE_CONTACT_PHONE_DISPLAY"], CANONICAL_DISPLAY
        )
        self.assertEqual(response.context["STORE_WHATSAPP_DIGITS"], CANONICAL_DIGITS)


class MobileStylesheetCoverageTests(SimpleTestCase):
    def test_mobile_breakpoints_and_overflow_guards_exist(self):
        css_path = Path(settings.BASE_DIR) / "static" / "css" / "store.css"
        css = css_path.read_text(encoding="utf-8")
        self.assertIn("Mobile-wide resilience audit v15", css)
        self.assertIn("@media(max-width:767px)", css)
        self.assertIn("@media(max-width:480px)", css)
        self.assertIn("@media(max-width:360px)", css)
        self.assertIn("overflow-x:clip", css)
        self.assertIn(".management-table-wrap{max-width:100%;overflow-x:auto", css)
        self.assertIn(".phone-country-input{width:100%;min-width:0}", css)

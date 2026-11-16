from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    STORE_CONTACT_PHONE="+971504084006",
    WHATSAPP_NUMBER="+971504084006",
    STORE_CONTACT_EMAIL="info@haybatalsultan.com",
    STORE_SOCIAL_HANDLE="HaybatAlsultan",
)
class CoreUiTests(TestCase):
    def test_about_page_uses_official_copy(self):
        response = self.client.get(reverse("core:about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "هيبة السلطان متجر إماراتي متخصص")
        self.assertContains(response, "من أبوظبي")

    def test_supported_coming_soon_pages_render(self):
        for slug in ("gemstones", "rare-collectibles", "gifts"):
            with self.subTest(slug=slug):
                response = self.client.get(reverse("core:coming_soon", args=[slug]))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "مختارات تستحق الانتظار")

    def test_unknown_coming_soon_slug_is_404(self):
        response = self.client.get(
            reverse("core:coming_soon", args=["not-a-real-section"])
        )
        self.assertEqual(response.status_code, 404)

    def test_footer_uses_current_contact_number_and_whatsapp(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "+971 50 408 4006")
        self.assertContains(response, "https://wa.me/971504084006")
        self.assertNotContains(response, "+971540484006")

    def test_footer_uses_official_email_and_social_handle(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "info@haybatalsultan.com")
        self.assertContains(response, "HaybatAlsultan")
        self.assertContains(response, "instagram.com/HaybatAlsultan")
        self.assertContains(response, "tiktok.com/@HaybatAlsultan")
        self.assertNotContains(response, "haybatalsutan")

    def test_first_visit_defaults_to_arabic_even_with_english_browser_header(self):
        response = self.client.get(
            reverse("core:home"), HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9"
        )
        self.assertContains(response, '<html lang="ar" dir="rtl">', html=False)

    def test_language_picker_can_switch_to_english(self):
        response = self.client.post(
            reverse("set_language"), {"language": "en", "next": reverse("core:home")}
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, '<html lang="en" dir="ltr">', html=False)

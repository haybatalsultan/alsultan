from urllib.parse import unquote

from django.test import TestCase
from django.urls import reverse


class DigitalServicesV204Tests(TestCase):
    def test_digital_services_page_is_public_and_professional(self):
        response = self.client.get(reverse("core:digital_services"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "digital-services-page")
        self.assertContains(response, "خدماتنا الأخرى")
        self.assertContains(response, "اطلب استشارة عبر واتساب")

    def test_consultation_whatsapp_link_has_fixed_source_identifier(self):
        response = self.client.get(reverse("core:digital_services"))
        self.assertEqual(response.status_code, 200)
        url = response.context["consultation_whatsapp_url"]
        decoded = unquote(url)
        self.assertTrue(url.startswith("https://wa.me/"))
        self.assertIn("HS-DIGITAL-SERVICES", decoded)
        self.assertIn("طلب استشارة", decoded)

    def test_query_string_cannot_override_whatsapp_message(self):
        attacker_text = "javascript:alert(1)-ATTACKER-CONTROLLED"
        response = self.client.get(
            reverse("core:digital_services"),
            {"text": attacker_text, "phone": "0000000000"},
        )
        self.assertEqual(response.status_code, 200)
        url = unquote(response.context["consultation_whatsapp_url"])
        self.assertNotIn(attacker_text, url)
        self.assertNotIn("0000000000", url)
        self.assertIn("HS-DIGITAL-SERVICES", url)

    def test_navigation_places_digital_services_after_contact(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        contact_pos = html.find("تواصل معنا")
        services_pos = html.find("خدماتنا الأخرى")
        self.assertGreaterEqual(contact_pos, 0)
        self.assertGreater(services_pos, contact_pos)

    def test_service_page_has_no_lead_capture_form(self):
        response = self.client.get(reverse("core:digital_services"))
        self.assertEqual(response.status_code, 200)

        # base.html intentionally contains a POST form for language switching.
        # The Digital Services page itself must not expose a consultation
        # capture form or user-controlled consultation fields.
        self.assertNotContains(response, 'class="consultation-form"')
        self.assertNotContains(response, 'name="consultation_message"')
        self.assertNotContains(response, 'name="consultation_phone"')


class HeroBrandingV204Tests(TestCase):
    def test_home_still_uses_official_branding_hero_asset(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="hero-image"')

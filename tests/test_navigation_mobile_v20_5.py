from django.test import TestCase
from django.urls import reverse


class NavigationMobileV205Tests(TestCase):
    def test_digital_services_stays_after_contact(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertGreater(html.find("خدماتنا الأخرى"), html.find("تواصل معنا"))

    def test_digital_services_nav_uses_globe_icon(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(
            response,
            '<use href="#icon-globe"></use>',
            html=True,
        )

    def test_mobile_nav_id_and_toggle_target_match(self):
        response = self.client.get(reverse("core:home"))
        html = response.content.decode("utf-8")
        # Desktop navigation remains available for >= 992px.
        self.assertIn('id="storeNav"', html)
        # Compact layouts use a separate off-canvas control.
        self.assertIn('id="mobileStoreMenu"', html)
        self.assertIn('data-bs-target="#mobileStoreMenu"', html)
        self.assertIn('data-bs-toggle="offcanvas"', html)

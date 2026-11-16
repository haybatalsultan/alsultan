from django.test import TestCase
from django.urls import reverse


class MobileHeaderV2061Tests(TestCase):
    def test_mobile_header_has_explicit_search_and_cart_controls(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn("header-search-icon", html)
        self.assertIn("header-cart-icon", html)
        self.assertIn('data-bs-target="#mobileStoreMenu"', html)

    def test_mobile_menu_button_is_not_a_link_or_user_controlled_url(self):
        marker = "javascript:alert(1)"
        response = self.client.get(reverse("core:home"), {"next": marker})
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn('class="mobile-menu-button"', html)
        self.assertIn('type="button"', html)
        self.assertNotIn(f'href="{marker}"', html)

    def test_desktop_nav_structure_remains_present(self):
        response = self.client.get(reverse("core:home"))
        html = response.content.decode("utf-8")
        self.assertIn('class="collapse main-nav-collapse"', html)
        self.assertIn('id="storeNav"', html)

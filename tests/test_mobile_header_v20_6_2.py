from django.test import TestCase
from django.urls import reverse


class MobileHeaderV2062Tests(TestCase):
    def test_mobile_menu_search_and_cart_share_header_actions_cluster(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")

        actions_start = html.find('<div class="header-actions">')
        actions_end = html.find("</div>", actions_start)
        self.assertGreaterEqual(actions_start, 0)
        self.assertGreater(actions_end, actions_start)

        cluster = html[actions_start:actions_end]
        self.assertIn("mobile-menu-button", cluster)
        self.assertIn("header-search-icon", cluster)
        self.assertIn("header-cart-icon", cluster)

    def test_mobile_menu_button_still_targets_offcanvas(self):
        response = self.client.get(reverse("core:home"))
        html = response.content.decode("utf-8")
        self.assertIn('data-bs-toggle="offcanvas"', html)
        self.assertIn('data-bs-target="#mobileStoreMenu"', html)

    def test_mobile_structure_does_not_replace_desktop_navigation(self):
        response = self.client.get(reverse("core:home"))
        html = response.content.decode("utf-8")
        self.assertIn('id="storeNav"', html)
        self.assertIn('class="collapse main-nav-collapse"', html)

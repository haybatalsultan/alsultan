from pathlib import Path

from django.test import TestCase
from django.urls import reverse


class DesktopNavSpacingV2071Tests(TestCase):
    def test_services_and_existing_action_icons_remain_present(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn("خدماتنا الأخرى", html)
        self.assertIn("header-actions", html)
        self.assertIn("header-search-icon", html)
        self.assertIn("header-cart-icon", html)

    def test_no_new_separator_markup_was_added(self):
        response = self.client.get(reverse("core:home"))
        html = response.content.decode("utf-8")
        self.assertNotIn("desktop-nav-separator", html)

    def test_desktop_spacing_is_scoped_above_mobile_breakpoint(self):
        css = (
            Path(__file__).resolve().parents[1] / "static" / "css" / "store.css"
        ).read_text(encoding="utf-8")
        marker = "v20.7.1 — Desktop navigation breathing space"
        self.assertIn(marker, css)
        block = css[css.index(marker) :]
        self.assertIn("@media(min-width:992px)", block)
        self.assertIn("margin-inline-start:.85rem", block)

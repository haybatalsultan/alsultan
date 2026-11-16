from pathlib import Path

from django.test import SimpleTestCase


class MobileCartFeedbackV20155Tests(SimpleTestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.js = (root / "static" / "js" / "cart-ui.js").read_text(encoding="utf-8")
        self.css = (root / "static" / "css" / "store.css").read_text(encoding="utf-8")

    def test_mobile_feedback_uses_server_cart_count(self):
        self.assertIn("setCartCount(data.cart_count)", self.js)
        self.assertNotIn("setCartCount(Number", self.js)

    def test_mobile_success_feedback_has_cart_action(self):
        self.assertIn("mobileProminent: true", self.js)
        self.assertIn("actionUrl: '/orders/cart/'", self.js)
        self.assertIn("عرض السلة", self.js)

    def test_mobile_does_not_depend_on_desktop_mini_cart(self):
        self.assertIn("if (!isMobileViewport())", self.js)
        self.assertIn("showMiniCart(data)", self.js)
        self.assertIn("cart-toast--mobile-prominent", self.css)

    def test_cart_badge_is_updated_from_all_server_rendered_nodes(self):
        self.assertIn("querySelectorAll('[data-cart-count]')", self.js)
        self.assertIn("node.textContent = String(count)", self.js)

    def test_reduced_motion_is_respected(self):
        self.assertIn("prefers-reduced-motion:reduce", self.css)
        self.assertIn("reducedMotion()", self.js)

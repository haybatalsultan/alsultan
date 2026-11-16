from pathlib import Path

from django.test import SimpleTestCase


class CartMotionV20182Tests(SimpleTestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.js = (root / "static" / "js" / "cart-ui.js").read_text(encoding="utf-8")
        self.css = (root / "static" / "css" / "store.css").read_text(encoding="utf-8")

    def test_mobile_bottom_sheet_uses_safe_dom_apis(self):
        self.assertIn("showMobileCartSheet(data)", self.js)
        self.assertIn("document.createElement", self.js)
        self.assertIn("textContent", self.js)
        self.assertNotIn("innerHTML", self.js)

    def test_mobile_sheet_is_accessible_and_dismissible(self):
        self.assertIn("aria-modal", self.js)
        self.assertIn("data-mobile-cart-close", self.js)
        self.assertIn("event.key === 'Escape'", self.js)

    def test_desktop_keeps_drawer_and_mobile_gets_sheet(self):
        self.assertIn("if (!isMobileViewport())", self.js)
        self.assertIn("showMiniCart(data)", self.js)
        self.assertIn("showMobileCartSheet(data)", self.js)
        self.assertIn(".mobile-cart-sheet", self.css)
        self.assertIn("@media(min-width:768px)", self.css)

    def test_reduced_motion_is_preserved(self):
        self.assertIn("prefers-reduced-motion:reduce", self.css)
        self.assertIn("reducedMotion()", self.js)

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product
from orders.models import Cart, CartItem


class StorefrontCartUXV2073Tests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name_ar="المسابيح",
            name_en="Misbah",
            sort_order=1,
            is_active=True,
        )
        self.product = Product.objects.create(
            name_ar="مسباح اختبار السلة",
            name_en="Cart Test Misbah",
            category=self.category,
            cost_price=Decimal("100.00"),
            selling_price=Decimal("250.00"),
            available_quantity=3,
            reserved_quantity=0,
            status=Product.Status.AVAILABLE,
        )

    def _ajax(self):
        return {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

    def test_misbah_navigation_alias_resolves_immutable_category_slug(self):
        self.assertNotEqual(self.category.slug, "misbah")
        response = self.client.get(reverse("catalog:list"), {"category": "misbah"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name_ar)
        self.assertEqual(response.context["selected_category"], self.category.slug)

    def test_ajax_add_returns_cart_count_without_redirect(self):
        response = self.client.post(
            reverse("orders:cart_add", args=[self.product.public_id]),
            {"quantity": "1"},
            **self._ajax(),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["cart_count"], 1)
        self.assertEqual(payload["quantity"], 1)
        self.assertEqual(payload["unit_price"], "250.00")

    def test_quantity_endpoint_cannot_exceed_available_stock(self):
        self.client.get(reverse("orders:cart"))
        cart = Cart.objects.get(session_key=self.client.session.session_key)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        response = self.client.post(
            reverse("orders:cart_quantity", args=[item.id]),
            {"quantity": "4"},
            **self._ajax(),
        )
        self.assertEqual(response.status_code, 400)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    def test_ajax_remove_only_removes_item_from_current_cart(self):
        self.client.get(reverse("orders:cart"))
        cart = Cart.objects.get(session_key=self.client.session.session_key)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        response = self.client.post(
            reverse("orders:cart_remove", args=[item.id]),
            **self._ajax(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())
        self.assertEqual(response.json()["cart_count"], 0)

    def test_cart_page_renders_quantity_and_remove_controls(self):
        self.client.post(
            reverse("orders:cart_add", args=[self.product.public_id]), {"quantity": "1"}
        )
        response = self.client.get(reverse("orders:cart"))
        self.assertContains(response, "data-cart-quantity-form")
        self.assertContains(response, "data-cart-remove-form")
        self.assertContains(response, self.product.sku)

    def test_fully_reserved_product_is_not_shown_on_storefront(self):
        self.product.reserved_quantity = self.product.available_quantity
        self.product.save(update_fields=["reserved_quantity", "updated_at"])
        response = self.client.get(reverse("catalog:list"), {"category": "misbah"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.product.name_ar)

    def test_ajax_unavailable_error_is_localized_and_does_not_leak_internal_message(
        self,
    ):
        self.product.reserved_quantity = self.product.available_quantity
        self.product.save(update_fields=["reserved_quantity", "updated_at"])
        response = self.client.post(
            reverse("orders:cart_add", args=[self.product.public_id]),
            {"quantity": "1"},
            **self._ajax(),
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertIn("غير متاحة", payload["message"])
        self.assertNotIn("Requested quantity", payload["message"])

    def test_add_payload_marks_stock_limit_for_unique_item(self):
        self.product.available_quantity = 1
        self.product.reserved_quantity = 0
        self.product.save(
            update_fields=["available_quantity", "reserved_quantity", "updated_at"]
        )
        response = self.client.post(
            reverse("orders:cart_add", args=[self.product.public_id]),
            {"quantity": "1"},
            **self._ajax(),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["stock_limit_reached"])
        self.assertEqual(payload["free_quantity"], 1)
        self.assertEqual(payload["cart_item_quantity"], 1)

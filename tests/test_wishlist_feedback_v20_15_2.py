from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import Category, Product, WishlistItem


class WishlistFeedbackV20152Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="wishlist152", password="StrongPass!12345", role=User.Role.CUSTOMER
        )
        self.category = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="wishlist-v20152", is_active=True
        )
        self.product = Product.objects.create(
            category=self.category,
            name_ar="اختبار المفضلة",
            name_en="Wishlist test",
            available_quantity=1,
            reserved_quantity=0,
            cost_price="50.00",
            selling_price="100.00",
            status=Product.Status.AVAILABLE,
        )
        self.url = reverse("catalog:wishlist_toggle", args=[self.product.public_id])
        self.client.login(username="wishlist152", password="StrongPass!12345")

    def test_ajax_add_and_remove_returns_explicit_state(self):
        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["wishlisted"])
        self.assertTrue(
            WishlistItem.objects.filter(user=self.user, product=self.product).exists()
        )

        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["wishlisted"])
        self.assertFalse(
            WishlistItem.objects.filter(user=self.user, product=self.product).exists()
        )

    def test_get_cannot_toggle_wishlist(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertFalse(
            WishlistItem.objects.filter(user=self.user, product=self.product).exists()
        )

    def test_anonymous_user_cannot_toggle_wishlist(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(WishlistItem.objects.filter(product=self.product).exists())

    def test_reserved_public_item_can_remain_a_wishlist_reference(self):
        self.product.reserved_quantity = 1
        self.product.save(update_fields=["reserved_quantity"])
        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["wishlisted"])
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_quantity, 1)

    def test_detail_renders_current_wishlist_state(self):
        WishlistItem.objects.create(user=self.user, product=self.product)
        response = self.client.get(
            reverse("catalog:detail", args=[self.product.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'class="header-icon header-wishlist-icon has-items"',
        )
        self.assertContains(response, "data-wishlist-count>1</span>")
        self.assertContains(response, "mobile-wishlist-link has-items")

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import Category, Product, WishlistItem


class WishlistHeaderSyncV20154Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="wish154", password="StrongPass!12345", role=User.Role.CUSTOMER
        )
        self.category = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="wish-154", is_active=True
        )
        self.product = Product.objects.create(
            category=self.category,
            name_ar="اختبار",
            name_en="Test",
            available_quantity=1,
            reserved_quantity=0,
            cost_price="50.00",
            selling_price="100.00",
            status=Product.Status.AVAILABLE,
        )
        self.client.login(username="wish154", password="StrongPass!12345")

    def test_header_is_red_state_and_badged_when_wishlist_has_items(self):
        WishlistItem.objects.create(user=self.user, product=self.product)
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "data-wishlist-header")
        self.assertContains(response, "header-wishlist-icon has-items")
        self.assertContains(response, "data-wishlist-count>1</span>", html=False)

    def test_ajax_toggle_returns_server_side_wishlist_count(self):
        url = reverse("catalog:wishlist_toggle", args=[self.product.public_id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["wishlist_count"], 1)
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["wishlist_count"], 0)

    def test_guest_header_does_not_expose_wishlist_count(self):
        self.client.logout()
        WishlistItem.objects.create(user=self.user, product=self.product)
        response = self.client.get(reverse("core:home"))
        self.assertNotContains(response, "data-wishlist-header")

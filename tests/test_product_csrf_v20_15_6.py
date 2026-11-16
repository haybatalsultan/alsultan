from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Category, Product


class ProductCsrfV20156Tests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name_ar="مسابيح",
            name_en="Misbah",
            slug="csrf-v20156",
            is_active=True,
        )
        self.product = Product.objects.create(
            category=self.category,
            name_ar="اختبار CSRF",
            name_en="CSRF test",
            available_quantity=1,
            reserved_quantity=0,
            cost_price="50.00",
            selling_price="100.00",
            status=Product.Status.AVAILABLE,
        )
        self.detail_url = reverse("catalog:detail", args=[self.product.public_id])
        self.cart_add_url = reverse("orders:cart_add", args=[self.product.public_id])

    def test_product_detail_issues_csrf_cookie(self):
        client = Client(enforce_csrf_checks=True)
        response = client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)
        self.assertTrue(response.cookies["csrftoken"].value)

    def test_cart_add_without_csrf_is_rejected(self):
        client = Client(enforce_csrf_checks=True)

        response = client.post(
            self.cart_add_url,
            {"quantity": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 403)

    def test_cart_add_with_csrf_cookie_and_header_succeeds(self):
        client = Client(enforce_csrf_checks=True)
        detail_response = client.get(self.detail_url)
        token = detail_response.cookies["csrftoken"].value

        response = client.post(
            self.cart_add_url,
            {"quantity": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("ok", True))
        self.assertEqual(payload["cart_count"], 1)

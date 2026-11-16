from decimal import Decimal

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Category, Product


class PublicItemCodeTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name_ar="مسابيح", name_en="Misbah")
        self.product = Product.objects.create(
            name_ar="مسبحة كهرمان",
            name_en="Amber Misbah",
            category=self.category,
            cost_price=Decimal(100),
            selling_price=Decimal(200),
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )

    def test_item_code_uses_public_hs_format(self):
        self.assertEqual(self.product.sku, f"HS{self.product.pk:05d}")

    def test_exact_item_code_search_redirects_to_product(self):
        response = self.client.get(
            reverse("catalog:list"), {"q": self.product.sku.lower()}
        )
        self.assertRedirects(
            response, reverse("catalog:detail", args=[self.product.public_id])
        )

    def test_exact_item_code_does_not_redirect_to_non_available_product(self):
        self.product.status = Product.Status.SOLD
        self.product.save(update_fields=["status"])
        response = self.client.get(
            reverse("catalog:list"),
            {"q": self.product.sku.lower()},
        )
        self.assertEqual(response.status_code, 200)

    def test_product_page_labels_public_item_code(self):
        response = self.client.get(
            reverse("catalog:detail", args=[self.product.public_id])
        )
        self.assertContains(response, self.product.sku)
        self.assertContains(response, "رقم القطعة")


class LiveViewerTests(TestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name_ar="نوادر", name_en="Rare")
        self.product = Product.objects.create(
            name_ar="قطعة نادرة",
            name_en="Rare Item",
            category=self.category,
            cost_price=Decimal(100),
            selling_price=Decimal(200),
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )
        self.url = reverse("catalog:viewers", args=[self.product.public_id])

    def tearDown(self):
        cache.clear()

    def test_same_browser_does_not_inflate_viewer_count(self):
        client = Client()
        first = client.post(self.url).json()["count"]
        second = client.post(self.url).json()["count"]
        self.assertEqual(first, 1)
        self.assertEqual(second, 1)

    def test_distinct_browser_sessions_count_separately(self):
        first = Client()
        second = Client()
        self.assertEqual(first.post(self.url).json()["count"], 1)
        self.assertEqual(second.post(self.url).json()["count"], 2)

    def test_viewer_endpoint_rejects_get(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_non_storefront_product_is_not_exposed(self):
        self.product.status = Product.Status.DRAFT
        self.product.save()
        self.assertEqual(self.client.post(self.url).status_code, 404)


class PremiumGallerySecurityTests(TestCase):
    def test_zoom_url_is_server_generated_cloudinary_delivery(self):
        from unittest.mock import patch

        from catalog.models import ProductImage

        image = ProductImage(
            cloudinary_public_id="haybatalsultan/products/test-safe",
            secure_url="https://res.cloudinary.com/demo/image/upload/test-safe.jpg",
        )
        with patch(
            "catalog.services.image_service.delivery_url",
            return_value="https://res.cloudinary.com/demo/image/upload/w_2400,c_limit/q_auto/f_auto/test-safe.jpg",
        ) as delivery:
            url = image.zoom_url
        self.assertTrue(url.startswith("https://"))
        delivery.assert_called_once_with(
            "haybatalsultan/products/test-safe", width=2400, height=None, crop="limit"
        )

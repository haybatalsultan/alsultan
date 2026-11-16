from io import BytesIO
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import SupervisorPermission, User
from catalog.models import Category, Product, ProductImage
from catalog.services.image_service import (
    attach_product_images,
    delete_product_image,
    set_primary_image,
    validate_image,
)
from tests.helpers import login_management


def image_upload(name="test.jpg", image_format="JPEG"):
    buffer = BytesIO()
    Image.new("RGB", (800, 800), "white").save(buffer, format=image_format)
    content_type = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }.get(image_format, "image/jpeg")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


@override_settings(
    CLOUDINARY_CLOUD_NAME="test-cloud",
    CLOUDINARY_API_KEY="test-key",
    CLOUDINARY_API_SECRET="test-secret",
    PRODUCT_IMAGE_MAX_BYTES=5 * 1024 * 1024,
    PRODUCT_IMAGE_MAX_COUNT=12,
    PRODUCT_IMAGE_MAX_PIXELS=40_000_000,
)
class ProductImageServiceTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            name_ar="مسابيح",
            name_en="Misbah",
            slug="misbah-images",
        )
        self.product = Product.objects.create(
            sku="HS-IMG-1",
            name_ar="مسبحة اختبار",
            name_en="Test Misbah",
            category=category,
            cost_price="10.00",
            selling_price="100.00",
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )

    def test_invalid_non_image_is_rejected(self):
        upload = SimpleUploadedFile(
            "attack.svg",
            b"<svg><script>alert(1)</script></svg>",
            content_type="image/svg+xml",
        )
        with self.assertRaises(ValidationError):
            validate_image(upload)

    @patch("cloudinary.uploader.upload")
    def test_attach_creates_primary_image_with_server_generated_path(self, upload_mock):
        upload_mock.return_value = {
            "public_id": f"haybatalsultan/products/{self.product.product_reference}/img-safe",
            "secure_url": "https://res.cloudinary.com/test/image/upload/img-safe.jpg",
            "asset_id": "asset123",
            "width": 800,
            "height": 800,
            "bytes": 5000,
            "format": "jpg",
        }
        created = attach_product_images(self.product, [image_upload()])
        self.assertEqual(len(created), 1)
        image = created[0]
        self.assertTrue(image.is_primary)
        self.assertEqual(image.product, self.product)
        self.assertTrue(
            image.cloudinary_public_id.startswith(
                f"haybatalsultan/products/{self.product.product_reference}/"
            )
        )

        kwargs = upload_mock.call_args.kwargs
        self.assertEqual(
            kwargs["asset_folder"],
            f"haybatalsultan/products/{self.product.product_reference}",
        )
        self.assertNotIn("api_secret", kwargs)

    def test_delivery_url_falls_back_when_cloudinary_name_missing(self):
        image = ProductImage.objects.create(
            product=self.product,
            cloudinary_public_id="x/y",
            secure_url="https://example.test/original.jpg",
            is_primary=True,
        )
        with self.settings(CLOUDINARY_CLOUD_NAME=""):
            self.assertEqual(image.card_url, image.secure_url)

    def test_set_primary_image_is_atomic_for_product(self):
        first = ProductImage.objects.create(
            product=self.product,
            cloudinary_public_id="product/first",
            secure_url="https://example.test/first.jpg",
            is_primary=True,
        )
        second = ProductImage.objects.create(
            product=self.product,
            cloudinary_public_id="product/second",
            secure_url="https://example.test/second.jpg",
        )
        set_primary_image(second)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_primary)
        self.assertTrue(second.is_primary)

    @patch("cloudinary.uploader.destroy")
    def test_delete_primary_promotes_next_image(self, destroy_mock):
        destroy_mock.return_value = {"result": "ok"}
        first = ProductImage.objects.create(
            product=self.product,
            cloudinary_public_id="product/first",
            secure_url="https://example.test/first.jpg",
            sort_order=1,
            is_primary=True,
        )
        second = ProductImage.objects.create(
            product=self.product,
            cloudinary_public_id="product/second",
            secure_url="https://example.test/second.jpg",
            sort_order=2,
        )
        delete_product_image(first)
        self.assertFalse(ProductImage.objects.filter(pk=first.pk).exists())
        second.refresh_from_db()
        self.assertTrue(second.is_primary)


class ProductImagePermissionTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            name_ar="مسابيح",
            name_en="Misbah",
            slug="misbah-image-permission",
        )
        self.product = Product.objects.create(
            sku="HS-IMG-PERM",
            name_ar="مسبحة",
            name_en="Misbah",
            category=category,
            cost_price="10.00",
            selling_price="100.00",
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )
        self.supervisor = User.objects.create_user(
            username="image-supervisor",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        self.permissions = SupervisorPermission.objects.create(
            user=self.supervisor,
            view_products=True,
            manage_product_images=False,
        )
        login_management(self.client, self.supervisor, "VeryStrongPass!123")

    def test_supervisor_without_image_permission_is_forbidden(self):
        response = self.client.get(
            reverse("core:management_product_images", args=[self.product.public_id])
        )
        self.assertEqual(response.status_code, 403)

    def test_supervisor_with_image_permission_can_open_manager(self):
        self.permissions.manage_product_images = True
        self.permissions.save(update_fields=["manage_product_images"])
        response = self.client.get(
            reverse("core:management_product_images", args=[self.product.public_id])
        )
        self.assertEqual(response.status_code, 200)

    def test_image_delete_rejects_get(self):
        self.permissions.manage_product_images = True
        self.permissions.save(update_fields=["manage_product_images"])
        image = ProductImage.objects.create(
            product=self.product,
            cloudinary_public_id="p/i",
            secure_url="https://example.test/i.jpg",
            is_primary=True,
        )
        response = self.client.get(
            reverse(
                "core:management_product_image_delete",
                args=[self.product.public_id, image.public_id],
            )
        )
        self.assertEqual(response.status_code, 405)

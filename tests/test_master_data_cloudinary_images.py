from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from accounts.models import SupervisorPermission, User
from catalog.models import Category, Material
from tests.helpers import login_management


def make_image(name="master.jpg"):
    buffer = BytesIO()
    Image.new("RGB", (500, 500), "white").save(buffer, format="JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


class MasterDataCloudinaryImageTests(TestCase):
    def setUp(self):
        self.supervisor = User.objects.create_user(
            username="master-data-supervisor",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        SupervisorPermission.objects.create(
            user=self.supervisor,
            manage_master_data=True,
        )
        login_management(self.client, self.supervisor, "VeryStrongPass!123")

    def test_category_form_no_longer_accepts_manual_cloudinary_url(self):
        response = self.client.get(reverse("core:management_category_create"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="image_url"')
        self.assertContains(response, 'type="file"')

    def test_material_form_supports_direct_image_upload(self):
        response = self.client.get(reverse("core:management_material_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'type="file"')

    @patch("core.management_views.upload_master_data_image")
    def test_category_upload_path_is_server_controlled(self, upload_mock):
        upload_mock.return_value = (
            {
                "public_id": "haybatalsultan/categories/server-generated",
                "secure_url": "https://res.cloudinary.com/test/image/upload/category.jpg",
            },
            {"width": 500, "height": 500, "format": "jpeg", "bytes": 1000},
        )

        response = self.client.post(
            reverse("core:management_category_create"),
            {
                "name_ar": "مسابيح اختبار",
                "name_en": "Test Misbah",
                "sort_order": 10,
                "is_active": "on",
                "image": make_image(),
            },
        )
        self.assertEqual(response.status_code, 302)
        category = Category.objects.get(name_en="Test Misbah")
        self.assertEqual(
            category.image_public_id,
            "haybatalsultan/categories/server-generated",
        )
        kwargs = upload_mock.call_args.kwargs
        self.assertEqual(kwargs["kind"], "categories")
        self.assertEqual(kwargs["public_id"], category.public_id)

    @patch("core.management_views.upload_master_data_image")
    def test_material_upload_is_saved_without_browser_supplied_url(self, upload_mock):
        upload_mock.return_value = (
            {
                "public_id": "haybatalsultan/materials/server-generated",
                "secure_url": "https://res.cloudinary.com/test/image/upload/material.jpg",
            },
            {"width": 500, "height": 500, "format": "jpeg", "bytes": 1000},
        )

        response = self.client.post(
            reverse("core:management_material_create"),
            {
                "name_ar": "كهرمان اختبار",
                "name_en": "Test Amber",
                "sort_order": 20,
                "is_active": "on",
                "image": make_image(),
            },
        )
        self.assertEqual(response.status_code, 302)
        material = Material.objects.get(name_en="Test Amber")
        self.assertEqual(
            material.image_public_id,
            "haybatalsultan/materials/server-generated",
        )

    def test_customer_cannot_access_master_data(self):
        self.client.logout()
        customer = User.objects.create_user(
            username="plain-customer",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )
        self.client.login(username="plain-customer", password="VeryStrongPass!123")
        response = self.client.get(reverse("core:management_category_create"))
        self.assertEqual(response.status_code, 403)

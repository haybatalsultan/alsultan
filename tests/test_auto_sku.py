from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import SupervisorPermission, User
from catalog.models import Category, Product
from tests.helpers import login_management


class AutomaticSKUTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name_ar="مسابيح SKU",
            name_en="SKU Misbah",
            slug="sku-misbah",
        )

    def make_product(self, name="One"):
        return Product.objects.create(
            name_ar=f"مسبحة {name}",
            name_en=f"Misbah {name}",
            category=self.category,
            cost_price=Decimal("0.00"),
            selling_price=Decimal("0.00"),
            available_quantity=0,
            status=Product.Status.DRAFT,
        )

    def test_new_products_receive_automatic_sku_from_database_identity(self):
        first = self.make_product("One")
        second = self.make_product("Two")

        self.assertEqual(first.sku, f"HS{first.pk:05d}")
        self.assertEqual(second.sku, f"HS{second.pk:05d}")
        self.assertNotEqual(first.sku, second.sku)

    def test_direct_orm_supplied_sku_is_ignored_for_new_product(self):
        product = Product.objects.create(
            sku="MANUAL-SHOULD-NOT-WIN",
            name_ar="مسبحة ORM",
            name_en="ORM Misbah",
            category=self.category,
            cost_price=Decimal("0.00"),
            selling_price=Decimal("0.00"),
            status=Product.Status.DRAFT,
        )
        self.assertEqual(product.sku, f"HS{product.pk:05d}")
        self.assertNotEqual(product.sku, "MANUAL-SHOULD-NOT-WIN")

    def test_existing_sku_is_immutable(self):
        product = self.make_product()
        original = product.sku
        product.sku = "HS99999"
        with self.assertRaises(ValidationError):
            product.save()
        product.refresh_from_db()
        self.assertEqual(product.sku, original)

    def test_product_reference_and_sku_are_independent(self):
        product = self.make_product()
        self.assertTrue(product.product_reference.startswith("HSP-"))
        self.assertTrue(product.sku.startswith("HS"))
        self.assertNotEqual(product.product_reference, product.sku)


class AutomaticSKUManagementTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name_ar="مسابيح إدارة SKU",
            name_en="SKU Management Misbah",
            slug="sku-management-misbah",
        )
        self.supervisor = User.objects.create_user(
            username="sku-supervisor",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        SupervisorPermission.objects.create(
            user=self.supervisor,
            view_products=True,
            create_products=True,
            edit_products=True,
        )
        login_management(self.client, self.supervisor, "VeryStrongPass!123")

    def test_create_form_does_not_expose_sku_input(self):
        response = self.client.get(reverse("core:management_product_create"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="sku"')
        self.assertContains(response, "HS00001")

    def test_create_page_shows_last_persisted_item_code_without_predicting_next(self):
        first = Product.objects.create(
            name_ar="مسبحة موجودة",
            name_en="Existing Misbah",
            category=self.category,
            cost_price=Decimal("0.00"),
            selling_price=Decimal("0.00"),
            available_quantity=0,
            status=Product.Status.DRAFT,
        )
        response = self.client.get(reverse("core:management_product_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, first.sku)
        self.assertNotContains(response, f"HS{first.pk + 1:05d}")

    def test_products_page_shows_last_persisted_item_code(self):
        first = Product.objects.create(
            name_ar="مسبحة أولى",
            name_en="First Existing Misbah",
            category=self.category,
            cost_price=Decimal("0.00"),
            selling_price=Decimal("0.00"),
            available_quantity=0,
            status=Product.Status.DRAFT,
        )
        second = Product.objects.create(
            name_ar="مسبحة ثانية",
            name_en="Second Existing Misbah",
            category=self.category,
            cost_price=Decimal("0.00"),
            selling_price=Decimal("0.00"),
            available_quantity=0,
            status=Product.Status.DRAFT,
        )
        response = self.client.get(reverse("core:management_products"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, second.sku)
        self.assertContains(response, "last-item-code-chip")
        self.assertNotEqual(first.sku, second.sku)

    def test_created_product_success_message_uses_actual_server_generated_sku(self):
        response = self.client.post(
            reverse("core:management_product_create"),
            {
                "name_ar": "مسبحة رسالة",
                "name_en": "Message Misbah",
                "category": self.category.pk,
                "material": "",
                "origin": "",
                "color": "",
                "bead_count": "",
                "bead_size_mm": "",
                "weight_g": "",
                "shape": "",
                "tassel_type": "",
                "condition": "",
                "available_quantity": "0",
                "description_ar": "",
                "description_en": "",
                "meta_title_ar": "",
                "meta_title_en": "",
                "meta_description_ar": "",
                "meta_description_en": "",
                "is_featured": "",
                "is_new_arrival": "",
                "is_best_seller": "",
            },
            follow=True,
        )
        product = Product.objects.get(name_en="Message Misbah")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.sku)

    def test_posted_sku_is_ignored_and_server_generates_value(self):
        response = self.client.post(
            reverse("core:management_product_create"),
            {
                "sku": "ATTACKER-CONTROLLED-SKU",
                "name_ar": "مسبحة تلقائية",
                "name_en": "Automatic Misbah",
                "category": self.category.pk,
                "material": "",
                "origin": "",
                "color": "",
                "bead_count": "",
                "bead_size_mm": "",
                "weight_g": "",
                "shape": "",
                "tassel_type": "",
                "condition": "",
                "available_quantity": "0",
                "description_ar": "",
                "description_en": "",
                "meta_title_ar": "",
                "meta_title_en": "",
                "meta_description_ar": "",
                "meta_description_en": "",
                "is_featured": "",
                "is_new_arrival": "",
                "is_best_seller": "",
            },
        )
        self.assertEqual(response.status_code, 302)

        product = Product.objects.get(name_en="Automatic Misbah")
        self.assertEqual(product.sku, f"HS{product.pk:05d}")
        self.assertNotEqual(product.sku, "ATTACKER-CONTROLLED-SKU")

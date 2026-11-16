from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from catalog.models import Category, Product, ProductCustodyHistory
from tests.helpers import login_management


class ProductCustodyUXV20815Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="custody-ux-owner",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        self.customer = User.objects.create_user(
            username="custody-ux-customer",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )
        category = Category.objects.create(
            name_ar="مسابيح",
            name_en="Misbah",
            slug="custody-ux",
        )
        self.product = Product.objects.create(
            name_ar="مسباح يسر كلاسيكي ثقيل",
            name_en="Classic Yusr Misbah",
            category=category,
            cost_price=Decimal("500.00"),
            selling_price=Decimal("1200.00"),
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )
        login_management(self.client, self.owner, "VeryStrongPass!123")

    def url(self):
        return reverse(
            "core:management_product_custody",
            args=[self.product.public_id],
        )

    def test_arabic_page_has_localized_professional_fields(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        for text in (
            "الموقع الحالي المسجل",
            "تسجيل حركة جديدة",
            "المكان",
            "القطعة موجودة لدى",
            "تاريخ وضع القطعة",
            "سجل حركة القطعة",
        ):
            self.assertContains(response, text)
        self.assertNotContains(response, "Location name:")
        self.assertNotContains(response, "Holder name:")

    def test_recorded_movement_is_visible_and_current(self):
        response = self.client.post(
            self.url(),
            {
                "location_name": "  المحل الرئيسي  ",
                "holder_name": "  أحمد  ",
                "placed_on": timezone.localdate().isoformat(),
                "note": " للعرض فقط ",
            },
        )
        self.assertEqual(response.status_code, 302)
        entry = ProductCustodyHistory.objects.get(product=self.product)
        self.assertEqual(entry.location_name, "المحل الرئيسي")
        self.assertEqual(entry.holder_name, "أحمد")
        self.assertEqual(entry.note, "للعرض فقط")
        response = self.client.get(self.url())
        self.assertContains(response, "المحل الرئيسي")
        self.assertContains(response, "الحالي")
        self.assertContains(response, "custody-ux-owner")

    def test_custody_history_remains_append_only(self):
        entry = ProductCustodyHistory.objects.create(
            product=self.product,
            location_name="المخزن",
            placed_on=timezone.localdate(),
            recorded_by=self.owner,
        )
        with self.assertRaises(RuntimeError):
            ProductCustodyHistory.objects.filter(pk=entry.pk).update(
                location_name="Tampered"
            )

    def test_customer_cannot_open_owner_custody_page(self):
        self.client.logout()
        self.client.login(
            username="custody-ux-customer",
            password="VeryStrongPass!123",
        )
        self.assertIn(self.client.get(self.url()).status_code, {302, 403})

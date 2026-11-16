from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from catalog.models import Category, Product
from core.models import AuditLog
from tests.helpers import login_management


class DiscountSourceHistoryV20833Tests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user(username="discount-owner",password="VeryStrongPass!123",role=User.Role.OWNER)
        self.cat=Category.objects.create(name_ar="مسابيح",name_en="Misbah",slug="discount-history-v20833")
        self.p1=Product.objects.create(category=self.cat,name_ar="أ",name_en="A",cost_price=Decimal("100"),selling_price=Decimal("1000"),discount_price=Decimal("900"),available_quantity=1,status=Product.Status.AVAILABLE)
        self.p2=Product.objects.create(category=self.cat,name_ar="ب",name_en="B",cost_price=Decimal("100"),selling_price=Decimal("2000"),discount_price=Decimal("1500"),available_quantity=1,status=Product.Status.AVAILABLE)
        login_management(self.client,self.owner,"VeryStrongPass!123")

    def test_owner_can_clear_one_direct_discount_without_changing_selling_price(self):
        response=self.client.post(reverse("core:management_clear_direct_discount",args=[self.p1.public_id]),{"reason":"cleanup"})
        self.assertEqual(response.status_code,302)
        self.p1.refresh_from_db()
        self.assertIsNone(self.p1.discount_price)
        self.assertEqual(self.p1.selling_price,Decimal("1000"))
        self.assertTrue(AuditLog.objects.filter(action="direct_discount_cleared",object_reference=self.p1.product_reference).exists())

    def test_bulk_clear_requires_explicit_confirmation(self):
        self.client.post(reverse("core:management_clear_all_direct_discounts"),{})
        self.p1.refresh_from_db(); self.p2.refresh_from_db()
        self.assertIsNotNone(self.p1.discount_price)
        self.assertIsNotNone(self.p2.discount_price)

    def test_owner_can_clear_all_direct_discounts_only(self):
        response=self.client.post(reverse("core:management_clear_all_direct_discounts"),{"confirm":"CLEAR_ALL_DIRECT_DISCOUNTS","reason":"legacy cleanup"})
        self.assertEqual(response.status_code,302)
        self.p1.refresh_from_db(); self.p2.refresh_from_db()
        self.assertIsNone(self.p1.discount_price)
        self.assertIsNone(self.p2.discount_price)
        self.assertEqual(AuditLog.objects.filter(action="direct_discount_cleared").count(),2)

    def test_direct_discount_requires_reason_on_future_pricing_save(self):
        response=self.client.post(reverse("core:management_pricing",args=[self.p1.public_id]),{"cost_price":"100","selling_price":"1000","discount_price":"800","confirm_high_discount":"on","discount_reason":""})
        self.assertEqual(response.status_code,200)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.discount_price,Decimal("900"))
    def test_owner_can_open_dedicated_pricing_history(self):
        response=self.client.get(reverse("core:management_product_pricing_history",args=[self.p1.public_id]))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,"سجل")


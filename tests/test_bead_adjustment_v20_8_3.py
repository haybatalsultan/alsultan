from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from catalog.models import Category, Product
from core.models import StoreSetting
from orders.models import Cart, CartItem, Order, OrderItem
from tests.helpers import login_management


class BeadAdjustmentV2083Tests(TestCase):
    def setUp(self):
        self.category=Category.objects.create(name_ar="مسابيح",name_en="Misbah",slug="bead-v2083")
        self.product=Product.objects.create(category=self.category,name_ar="مسباح 99",name_en="99 Bead",bead_count=99,cost_price=Decimal("100"),selling_price=Decimal("200"),available_quantity=1,status=Product.Status.AVAILABLE)
        self.cart=None
        self.item=None
        self.owner=User.objects.create_user(username="bead-owner",password="VeryStrongPass!123",role=User.Role.OWNER)
        self.store,_=StoreSetting.objects.get_or_create(singleton=True)
        self.store.bead_adjustment_enabled=True
        self.store.save(update_fields=["bead_adjustment_enabled","updated_at"])

    def attach_cart(self):
        session=self.client.session
        if not session.session_key:
            session.create()
        self.cart=Cart.objects.create(session_key=session.session_key)
        self.item=CartItem.objects.create(cart=self.cart,product=self.product,quantity=1)

    def test_99_bead_product_accepts_any_integer_from_33_to_original(self):
        self.attach_cart()
        for requested in (33,34,47,66,88,98):
            response=self.client.post(reverse("orders:cart_bead_adjustment",args=[self.item.pk]),{"requested_bead_count":str(requested)})
            self.assertEqual(response.status_code,302)
            self.item.refresh_from_db()
            self.assertEqual(self.item.requested_bead_count,requested)

    def test_rejects_less_than_33_and_more_than_original(self):
        self.attach_cart()
        for requested in (0,20,32,100,120):
            self.client.post(reverse("orders:cart_bead_adjustment",args=[self.item.pk]),{"requested_bead_count":str(requested)})
            self.item.refresh_from_db()
            self.assertIsNone(self.item.requested_bead_count)

    def test_original_count_means_no_adjustment(self):
        self.attach_cart()
        self.client.post(reverse("orders:cart_bead_adjustment",args=[self.item.pk]),{"requested_bead_count":"99"})
        self.item.refresh_from_db()
        self.assertIsNone(self.item.requested_bead_count)

    def test_global_toggle_disables_service(self):
        self.store.bead_adjustment_enabled=False
        self.store.save(update_fields=["bead_adjustment_enabled","updated_at"])
        self.attach_cart()
        self.client.post(reverse("orders:cart_bead_adjustment",args=[self.item.pk]),{"requested_bead_count":"45"})
        self.item.refresh_from_db()
        self.assertIsNone(self.item.requested_bead_count)

    def test_owner_only_settings(self):
        login_management(self.client,self.owner,"VeryStrongPass!123")
        response=self.client.post(reverse("core:management_bead_adjustment_settings"),{"bead_adjustment_enabled":"on"})
        self.assertEqual(response.status_code,302)
        self.store.refresh_from_db()
        self.assertTrue(self.store.bead_adjustment_enabled)

    def test_order_item_snapshot_fields_exist(self):
        names={f.name for f in OrderItem._meta.fields}
        for name in ("original_bead_count_snapshot","requested_bead_count_snapshot","bead_adjustment_completed_at","bead_adjustment_completed_by"):
            self.assertIn(name,names)

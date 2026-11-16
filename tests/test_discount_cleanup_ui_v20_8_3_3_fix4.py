from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from catalog.models import Category, Product
from tests.helpers import login_management


class DiscountCleanupUiV20833Fix4Tests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user(username="cleanup-owner",password="VeryStrongPass!123",role=User.Role.OWNER)
        self.cat=Category.objects.create(name_ar="مسابيح",name_en="Misbah",slug="cleanup-ui-v20833")
        self.product=Product.objects.create(category=self.cat,name_ar="اختبار",name_en="Test",cost_price=Decimal("100"),selling_price=Decimal("1000"),discount_price=Decimal("900"),available_quantity=1,status=Product.Status.AVAILABLE)
        login_management(self.client,self.owner,"VeryStrongPass!123")

    def test_owner_sees_count_and_confirmation_dialog_when_direct_discounts_exist(self):
        response=self.client.get(reverse("core:management_products"))
        self.assertContains(response,"يوجد 1 خصم مباشر")
        self.assertContains(response,"تأكيد مسح الخصومات المباشرة")
        self.assertContains(response,"CLEAR_ALL_DIRECT_DISCOUNTS")

    def test_cleanup_redirect_shows_result_card_and_no_delete_button_when_zero_remain(self):
        response=self.client.post(reverse("core:management_clear_all_direct_discounts"),{"confirm":"CLEAR_ALL_DIRECT_DISCOUNTS","reason":"test"},follow=True)
        self.assertContains(response,"تم تنظيف الخصومات المباشرة")
        self.assertContains(response,"تم مسح 1 خصم مباشر")
        self.assertContains(response,"لم يتم تعديل أي Promotion")
        self.assertContains(response,"لا توجد خصومات مباشرة حاليًا")
        self.assertNotContains(response,"data-discount-modal-open")

    def test_invalid_confirmation_does_not_delete(self):
        self.client.post(reverse("core:management_clear_all_direct_discounts"),{"confirm":"NO"})
        self.product.refresh_from_db()
        self.assertEqual(self.product.discount_price,Decimal("900"))

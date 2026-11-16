from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from catalog.models import Category, Product, Promotion
from catalog.services.promotion_service import price_snapshot


class PriceTransparencyV20832Tests(TestCase):
    def setUp(self):
        self.cat=Category.objects.create(name_ar="مسابيح",name_en="Misbah",slug="price-audit-v20832")
        self.product=Product.objects.create(category=self.cat,name_ar="اختبار",name_en="Test",cost_price=Decimal("100"),selling_price=Decimal("1000"),available_quantity=1,status=Product.Status.AVAILABLE)
        self.owner=User.objects.create_user(username="price-audit-owner",password="VeryStrongPass!123",role=User.Role.OWNER)

    def test_expired_promotion_automatically_returns_to_base_price(self):
        now=timezone.now()
        Promotion.objects.create(name_ar="منتهي",name_en="Expired",scope=Promotion.Scope.ALL,discount_type=Promotion.DiscountType.PERCENT,discount_value=Decimal("15"),starts_at=now-timedelta(days=2),ends_at=now-timedelta(days=1),is_active=True,created_by=self.owner,updated_by=self.owner)
        snap=price_snapshot(self.product,at=now)
        self.assertEqual(snap["source"],"BASE")
        self.assertEqual(snap["final_price"],Decimal("1000.00"))

    def test_manual_product_discount_is_identified_as_product_source(self):
        self.product.discount_price=Decimal("900")
        self.product.save(update_fields=["discount_price","updated_at"])
        snap=price_snapshot(self.product)
        self.assertEqual(snap["source"],"PRODUCT")
        self.assertEqual(snap["final_price"],Decimal("900.00"))

    def test_active_promotion_is_identified_by_pricing_engine(self):
        now=timezone.now()
        promo=Promotion.objects.create(name_ar="نشط",name_en="Active",scope=Promotion.Scope.ALL,discount_type=Promotion.DiscountType.PERCENT,discount_value=Decimal("15"),starts_at=now-timedelta(hours=1),ends_at=now+timedelta(hours=1),is_active=True,created_by=self.owner,updated_by=self.owner)
        snap=price_snapshot(self.product,at=now)
        self.assertEqual(snap["source"],"PROMOTION")
        self.assertEqual(snap["promotion"],promo)
        self.assertEqual(snap["final_price"],Decimal("850.00"))

    def test_manual_and_promotion_do_not_stack_and_best_price_wins(self):
        self.product.discount_price=Decimal("800")
        self.product.save(update_fields=["discount_price","updated_at"])
        now=timezone.now()
        Promotion.objects.create(name_ar="نشط",name_en="Active",scope=Promotion.Scope.ALL,discount_type=Promotion.DiscountType.PERCENT,discount_value=Decimal("15"),starts_at=now-timedelta(hours=1),ends_at=now+timedelta(hours=1),is_active=True,created_by=self.owner,updated_by=self.owner)
        snap=price_snapshot(self.product,at=now)
        self.assertEqual(snap["source"],"PRODUCT")
        self.assertEqual(snap["final_price"],Decimal("800.00"))

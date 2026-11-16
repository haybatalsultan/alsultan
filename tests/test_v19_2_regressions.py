from decimal import Decimal

from django.test import TestCase

from catalog.models import Category, Product, Promotion
from core.forms import ManagementProductForm, PromotionManagementForm


class V192RegressionTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name_ar="مسابيح",
            name_en="Misbah",
            slug="v19-2-misbah",
        )

    def test_owner_product_form_omitted_verification_defaults_to_none(self):
        form = ManagementProductForm(
            data={
                "name_ar": "مسبحة جديدة",
                "name_en": "New Misbah",
                "category": str(self.category.pk),
                "available_quantity": "1",
            },
            allow_status=False,
            allow_verification=True,
        )
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save(commit=False)
        self.assertEqual(
            product.verification_status,
            Product.VerificationStatus.NONE,
        )

    def test_new_promotion_form_does_not_access_unsaved_m2m_manager(self):
        product = Product.objects.create(
            name_ar="مسبحة",
            name_en="Misbah",
            category=self.category,
            cost_price=Decimal("40.00"),
            selling_price=Decimal("100.00"),
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )
        form = PromotionManagementForm(
            data={
                "name_ar": "خصم خاطئ",
                "name_en": "Invalid Discount",
                "scope": Promotion.Scope.PRODUCTS,
                "products": [str(product.pk)],
                "discount_type": Promotion.DiscountType.FIXED,
                "discount_value": "100.00",
                "gift_quantity": "1",
                "starts_at": "2026-08-15T10:00",
                "ends_at": "2026-08-16T10:00",
                "priority": "0",
                "is_active": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("discount_value", form.errors)

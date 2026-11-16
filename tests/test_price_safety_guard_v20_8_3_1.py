from pathlib import Path
from decimal import Decimal
from django.test import TestCase
from core.forms import PricingForm


class PriceSafetyGuardV20831Tests(TestCase):
    def payload(self,selling,discount,confirm=False):
        data={"cost_price":"100.00","selling_price":str(selling),"discount_price":str(discount),"discount_reason":"اختبار خصم"}
        if confirm:data["confirm_high_discount"]="on"
        return data

    def test_discount_at_15_percent_does_not_require_confirmation(self):
        form=PricingForm(data=self.payload("100.00","85.00"))
        self.assertTrue(form.is_valid(),form.errors)

    def test_discount_above_15_percent_requires_confirmation(self):
        form=PricingForm(data=self.payload("100.00","84.99"))
        self.assertFalse(form.is_valid())
        self.assertIn("confirm_high_discount",form.errors)

    def test_high_discount_is_allowed_after_explicit_owner_confirmation(self):
        form=PricingForm(data=self.payload("2570.00","10.00",True))
        self.assertTrue(form.is_valid(),form.errors)
        self.assertEqual(form.high_discount_percent,Decimal("99.61"))

    def test_discount_price_equal_or_above_selling_price_is_invalid_even_with_confirmation(self):
        for discount in ("100.00","120.00"):
            form=PricingForm(data=self.payload("100.00",discount,True))
            self.assertFalse(form.is_valid())
            self.assertIn("discount_price",form.errors)

    def test_warning_threshold_is_exactly_15_percent(self):
        self.assertEqual(PricingForm.HIGH_DISCOUNT_WARNING_PERCENT,Decimal("15.00"))
    def test_generic_management_form_contains_price_guard_without_new_template_contract(self):
        root=Path(__file__).resolve().parents[1]
        template=(root/"templates/management/form.html").read_text(encoding="utf-8")
        self.assertIn("data-high-discount-warning",template)
        self.assertFalse((root/"templates/management/pricing_form.html").exists())


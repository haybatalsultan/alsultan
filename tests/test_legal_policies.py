from django.test import TestCase
from django.urls import reverse

from orders.forms import CheckoutForm
from orders.services.order_service import POLICY_VERSION


class LegalPolicyTests(TestCase):
    def test_all_public_policy_pages_render(self):
        for slug in (
            "shipping",
            "returns",
            "authenticity",
            "reservation-cancellation",
            "privacy",
            "terms",
            "faq",
        ):
            response = self.client.get(reverse("core:info", args=[slug]))
            self.assertEqual(response.status_code, 200, slug)

    def test_unknown_policy_is_404(self):
        self.assertEqual(
            self.client.get(reverse("core:info", args=["not-a-policy"])).status_code,
            404,
        )

    def test_checkout_policy_acceptance_is_required(self):
        form = CheckoutForm(
            data={
                "customer_name": "Test Customer",
                "customer_email": "",
                "customer_phone": "0501234567",
                "country": "AE",
                "emirate": "Abu Dhabi",
                "city": "Abu Dhabi",
                "area": "Abu Dhabi",
                "street": "",
                "building": "",
                "apartment_or_villa": "",
                "postal_code": "",
                "additional_notes": "",
                "latitude": "",
                "longitude": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("policy_acceptance", form.errors)

    def test_policy_version_constant_is_explicit(self):
        self.assertEqual(POLICY_VERSION, "1.0-2026-08-14")

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from accounts.models import User
from orders.models import Order, PaymentAttempt
from orders.services.stripe_service import reconcile_payment_attempt


class StripeObjectLike:
    """Minimal StripeObject-like test double: item access works, .get does not exist."""

    def __init__(self, values):
        self._values = values

    def __getitem__(self, key):
        return self._values[key]


class StripeReconciliationV2096Tests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            "reconcile-2096", password="StrongPass!123", role="CUSTOMER"
        )
        self.order = Order.objects.create(
            reference="HS-RECON-2096",
            user=user,
            customer_name="Reconcile 2096",
            customer_email="reconcile2096@example.com",
            customer_phone="+971501234567",
            country="AE",
            emirate="Abu Dhabi",
            city="Abu Dhabi",
            area="Khalifa City",
            street="",
            building="",
            apartment_or_villa="",
            postal_code="",
            additional_notes="",
            subtotal=Decimal("5255.00"),
            discount_total=0,
            tax_total=0,
            shipping_total=0,
            grand_total=Decimal("5255.00"),
            currency="AED",
            payment_status=Order.PaymentStatus.PENDING,
        )
        self.attempt = PaymentAttempt.objects.create(
            order=self.order,
            checkout_session_id="cs_test_v2096",
            status=PaymentAttempt.Status.OPEN,
            amount=Decimal("5255.00"),
            currency="AED",
        )

    def _stripe_object(self):
        metadata = StripeObjectLike(
            {
                "order_public_id": str(self.order.public_id),
                "order_reference": self.order.reference,
            }
        )
        return StripeObjectLike(
            {
                "id": self.attempt.checkout_session_id,
                "currency": "aed",
                "amount_total": 525500,
                "payment_status": "paid",
                "status": "complete",
                "payment_intent": "pi_test_v2096",
                "metadata": metadata,
            }
        )

    @override_settings(STRIPE_ENABLED=True, STRIPE_SECRET_KEY="sk_test_reconcile")
    @patch("orders.services.stripe_service._retrieve_checkout_session")
    def test_reconciliation_accepts_stripeobject_without_get(self, mock_retrieve):
        mock_retrieve.return_value = self._stripe_object()
        self.assertEqual(reconcile_payment_attempt(self.attempt), "paid")
        self.order.refresh_from_db()
        self.attempt.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertEqual(self.attempt.status, PaymentAttempt.Status.PAID)
        self.assertEqual(self.attempt.payment_intent_id, "pi_test_v2096")

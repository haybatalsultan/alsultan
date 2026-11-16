from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import MFADevice, User
from core.models import StoreSetting
from core.services.payment_policy import current_payment_policy
from orders.models import Order, PaymentAttempt
from orders.services.stripe_service import reconcile_order_payment


class StripeServerReconciliationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "reconcile-customer", password="StrongPass!123", role="CUSTOMER"
        )
        self.order = Order.objects.create(
            reference="HS-RECON-001",
            user=self.user,
            customer_name="Reconcile Test",
            customer_email="reconcile@example.com",
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
            checkout_session_id="cs_test_reconcile",
            status=PaymentAttempt.Status.OPEN,
            amount=Decimal("5255.00"),
            currency="AED",
        )

    def _remote(self, *, amount_total=525500, payment_status="paid", status="complete"):
        obj = {
            "id": self.attempt.checkout_session_id,
            "currency": "aed",
            "amount_total": amount_total,
            "payment_status": payment_status,
            "status": status,
            "payment_intent": "pi_test_reconcile",
            "metadata": {
                "order_public_id": str(self.order.public_id),
                "order_reference": self.order.reference,
            },
        }
        return obj

    @override_settings(STRIPE_ENABLED=True, STRIPE_SECRET_KEY="sk_test_reconcile")
    @patch("orders.services.stripe_service._retrieve_checkout_session")
    def test_server_reconciliation_marks_verified_remote_payment_paid(
        self, mock_retrieve
    ):
        mock_retrieve.return_value = self._remote()
        self.assertEqual(reconcile_order_payment(self.order), "paid")
        self.order.refresh_from_db()
        self.attempt.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertEqual(self.order.payment_method, Order.PaymentMethod.STRIPE)
        self.assertEqual(self.attempt.status, PaymentAttempt.Status.PAID)

    @override_settings(STRIPE_ENABLED=True, STRIPE_SECRET_KEY="sk_test_reconcile")
    @patch("orders.services.stripe_service._retrieve_checkout_session")
    def test_reconciliation_rejects_amount_mismatch_without_marking_paid(
        self, mock_retrieve
    ):
        mock_retrieve.return_value = self._remote(amount_total=1)
        with self.assertRaises(ValueError):
            reconcile_order_payment(self.order)
        self.order.refresh_from_db()
        self.attempt.refresh_from_db()
        self.assertNotEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertNotEqual(self.attempt.status, PaymentAttempt.Status.PAID)


class OwnerPaymentPolicyTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "payment-owner", password="StrongPass!123", role="OWNER"
        )
        MFADevice.objects.create(
            user=self.owner, secret="JBSWY3DPEHPK3PXP", enabled=True
        )

    def _login_owner(self):
        self.client.force_login(self.owner)
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session.save()

    @override_settings(STRIPE_ENABLED=True)
    def test_owner_can_enable_both_payment_methods(self):
        self._login_owner()
        response = self.client.post(
            reverse("core:management_payment_settings"),
            {
                "online_payment_enabled": "on",
                "whatsapp_checkout_enabled": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        setting = StoreSetting.objects.get(singleton=True)
        self.assertTrue(setting.online_payment_enabled)
        self.assertTrue(setting.whatsapp_checkout_enabled)
        policy = current_payment_policy()
        self.assertTrue(policy.online)
        self.assertTrue(policy.manual)

    @override_settings(STRIPE_ENABLED=True)
    def test_owner_cannot_disable_every_payment_method(self):
        StoreSetting.objects.create(
            singleton=True, online_payment_enabled=True, whatsapp_checkout_enabled=True
        )
        self._login_owner()
        self.client.post(reverse("core:management_payment_settings"), {})
        setting = StoreSetting.objects.get(singleton=True)
        self.assertTrue(setting.online_payment_enabled)
        self.assertTrue(setting.whatsapp_checkout_enabled)

    @override_settings(STRIPE_ENABLED=False)
    def test_owner_cannot_enable_online_when_stripe_is_not_configured(self):
        self._login_owner()
        self.client.post(
            reverse("core:management_payment_settings"),
            {
                "online_payment_enabled": "on",
                "whatsapp_checkout_enabled": "on",
            },
        )
        setting = StoreSetting.objects.get(singleton=True)
        self.assertFalse(setting.online_payment_enabled)
        self.assertTrue(setting.whatsapp_checkout_enabled)

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from catalog.models import Category, Product
from orders.models import Order, PaymentAttempt, Reservation, StripeWebhookEvent
from orders.services.inventory_service import reserve
from orders.services.stripe_service import process_webhook_event


class StripeWebhookSecurityTests(TestCase):
    @override_settings(STRIPE_ENABLED=True, STRIPE_WEBHOOK_SECRET="whsec_test_only")
    def test_webhook_rejects_missing_signature(self):
        response = self.client.post(
            reverse("orders:stripe_webhook"),
            data=b"{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(STRIPE_ENABLED=True, STRIPE_WEBHOOK_SECRET="whsec_test_only")
    @patch("orders.webhooks.process_webhook_event")
    @patch("orders.webhooks.stripe.Webhook.construct_event")
    def test_webhook_normalises_verified_stripe_object_before_processing(
        self, mock_construct_event, mock_process
    ):
        class VerifiedStripeEvent:
            def to_dict_recursive(self):
                return {
                    "id": "evt_sdk_object",
                    "type": "product.created",
                    "data": {"object": {"id": "prod_test"}},
                }

        mock_construct_event.return_value = VerifiedStripeEvent()
        response = self.client.post(
            reverse("orders:stripe_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=test-signature",
        )
        self.assertEqual(response.status_code, 200)
        mock_process.assert_called_once_with(
            {
                "id": "evt_sdk_object",
                "type": "product.created",
                "data": {"object": {"id": "prod_test"}},
            }
        )

    @override_settings(STRIPE_ENABLED=True, STRIPE_WEBHOOK_SECRET="whsec_test_only")
    @patch(
        "orders.webhooks.process_webhook_event",
        side_effect=RuntimeError("diagnostic sentinel"),
    )
    @patch("orders.webhooks.stripe.Webhook.construct_event")
    @patch("orders.webhooks.logger.exception")
    def test_webhook_logs_unexpected_exception_without_leaking_request_material(
        self, mock_log_exception, mock_construct_event, _mock_process
    ):
        mock_construct_event.return_value = {
            "id": "evt_diag",
            "type": "product.created",
            "data": {"object": {}},
        }
        response = self.client.post(
            reverse("orders:stripe_webhook"),
            data=b'{"sensitive":"payload-must-not-be-logged"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=signature-must-not-be-logged",
        )
        self.assertEqual(response.status_code, 500)
        mock_log_exception.assert_called_once()
        log_args = " ".join(str(value) for value in mock_log_exception.call_args.args)
        self.assertIn("stripe_webhook_processing_failed", log_args)
        self.assertNotIn("payload-must-not-be-logged", log_args)
        self.assertNotIn("signature-must-not-be-logged", log_args)
        self.assertNotIn("whsec_test_only", log_args)
        self.assertEqual(response.content, b"")


class StripePaymentReconciliationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "stripe-customer", password="StrongPassword!123", role="CUSTOMER"
        )
        self.order = Order.objects.create(
            reference="HS-TEST-STRIPE",
            user=self.user,
            customer_name="Stripe Test",
            customer_email="stripe@example.com",
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
            subtotal=Decimal("100.00"),
            discount_total=Decimal("0.00"),
            tax_total=Decimal("0.00"),
            shipping_total=Decimal("0.00"),
            grand_total=Decimal("100.00"),
            currency="AED",
        )
        self.attempt = PaymentAttempt.objects.create(
            order=self.order,
            checkout_session_id="cs_test_haybat",
            status=PaymentAttempt.Status.OPEN,
            amount=Decimal("100.00"),
            currency="AED",
        )

    def _session_event(self, event_id="evt_test_paid", **overrides):
        obj = {
            "id": "cs_test_haybat",
            "currency": "aed",
            "amount_total": 10000,
            "payment_status": "paid",
            "payment_intent": "pi_test_haybat",
            "metadata": {
                "order_public_id": str(self.order.public_id),
                "order_reference": self.order.reference,
            },
        }
        obj.update(overrides)
        return {
            "id": event_id,
            "type": "checkout.session.completed",
            "data": {"object": obj},
        }

    def test_verified_paid_session_confirms_payment_and_order(self):
        self.assertTrue(process_webhook_event(self._session_event()))
        self.order.refresh_from_db()
        self.attempt.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertEqual(self.order.payment_method, Order.PaymentMethod.STRIPE)
        self.assertEqual(self.attempt.status, PaymentAttempt.Status.PAID)
        self.assertEqual(self.attempt.payment_intent_id, "pi_test_haybat")
        self.assertTrue(
            StripeWebhookEvent.objects.filter(event_id="evt_test_paid").exists()
        )

    def test_duplicate_event_is_idempotent(self):
        event = self._session_event()
        self.assertTrue(process_webhook_event(event))
        self.assertFalse(process_webhook_event(event))
        self.assertEqual(
            StripeWebhookEvent.objects.filter(event_id="evt_test_paid").count(), 1
        )

    def test_amount_mismatch_is_rejected_without_recording_event(self):
        with self.assertRaises(ValueError):
            process_webhook_event(
                self._session_event(event_id="evt_bad_amount", amount_total=9999)
            )
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.UNPAID)
        self.assertFalse(
            StripeWebhookEvent.objects.filter(event_id="evt_bad_amount").exists()
        )

    def test_expired_checkout_releases_reserved_inventory(self):
        category = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="stripe-misbah"
        )
        product = Product.objects.create(
            sku="HS-STRIPE-1",
            name_ar="قطعة Stripe",
            name_en="Stripe Piece",
            category=category,
            cost_price=Decimal("10.00"),
            selling_price=Decimal("100.00"),
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )
        reserve(product.pk, 1, self.order.reference, self.user)
        Reservation.objects.create(
            order=self.order,
            product=product,
            quantity=1,
            expires_at=self.attempt.created_at,
        )
        expired = self._session_event(event_id="evt_expired")
        expired["type"] = "checkout.session.expired"
        expired["data"]["object"]["payment_status"] = "unpaid"
        process_webhook_event(expired)
        product.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(product.reserved_quantity, 0)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)


class StripeOrderDetailRetryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "stripe-detail-customer", password="StrongPassword!123", role="CUSTOMER"
        )
        self.order = Order.objects.create(
            reference="HS-TEST-DETAIL",
            user=self.user,
            customer_name="Stripe Detail",
            customer_email="detail@example.com",
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
            subtotal=Decimal("100.00"),
            discount_total=Decimal("0.00"),
            tax_total=Decimal("0.00"),
            shipping_total=Decimal("0.00"),
            grand_total=Decimal("100.00"),
            currency="AED",
        )
        self.client.force_login(self.user)

    @override_settings(STRIPE_ENABLED=True)
    def test_unpaid_order_detail_offers_server_side_stripe_retry(self):
        category = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="detail-retry-misbah"
        )
        product = Product.objects.create(
            sku="HS-DETAIL-RETRY",
            name_ar="قطعة إعادة الدفع",
            name_en="Retry Piece",
            category=category,
            cost_price=Decimal("10.00"),
            selling_price=Decimal("100.00"),
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )
        reserve(product.pk, 1, self.order.reference, self.user)
        Reservation.objects.create(
            order=self.order,
            product=product,
            quantity=1,
            expires_at=self.order.created_at + timezone.timedelta(minutes=15),
        )
        response = self.client.get(
            reverse("orders:detail", args=[self.order.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("orders:stripe_payment_start", args=[self.order.public_id]),
        )
        self.assertContains(response, "الدفع الآن عبر Stripe")
        self.assertContains(response, "csrfmiddlewaretoken")

    @override_settings(STRIPE_ENABLED=True)
    def test_paid_order_detail_does_not_offer_another_payment(self):
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.status = Order.Status.CONFIRMED
        self.order.save(update_fields=["payment_status", "status", "updated_at"])
        response = self.client.get(
            reverse("orders:detail", args=[self.order.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            reverse("orders:stripe_payment_start", args=[self.order.public_id]),
        )
        self.assertContains(response, "تم استلام الدفعة")

    @override_settings(STRIPE_ENABLED=True)
    def test_cancelled_order_detail_does_not_offer_payment_retry(self):
        self.order.status = Order.Status.CANCELLED
        self.order.save(update_fields=["status", "updated_at"])
        response = self.client.get(
            reverse("orders:detail", args=[self.order.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            reverse("orders:stripe_payment_start", args=[self.order.public_id]),
        )

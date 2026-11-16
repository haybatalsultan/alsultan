from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from catalog.models import Category, Product
from orders.models import Order, PaymentAttempt, Reservation
from orders.services.inventory_service import reserve
from orders.services.reservation_service import expire_unpaid_order_if_needed

User = get_user_model()


@override_settings(
    STRIPE_ENABLED=True,
    STRIPE_SECRET_KEY="sk_test_placeholder",
    RESERVATION_MINUTES=10,
    STRIPE_CHECKOUT_MINUTES=30,
)
class ReservationStrategyV2015Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("strategy15", password="StrongPass!12345")
        self.category = Category.objects.create(name_ar="مسابيح", name_en="Misbah")
        self.product = Product.objects.create(
            category=self.category,
            name_ar="قطعة استراتيجية",
            name_en="Strategy piece",
            available_quantity=1,
            reserved_quantity=0,
            cost_price=Decimal("10.00"),
            selling_price=Decimal("100.00"),
            status=Product.Status.AVAILABLE,
        )
        self.order = Order.objects.create(
            reference="HS-STRATEGY-15",
            user=self.user,
            customer_name="Customer",
            customer_phone="+971501234567",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("100.00"),
            grand_total=Decimal("100.00"),
            currency="AED",
        )
        reserve(self.product.pk, 1, self.order.reference, self.user)
        self.reservation = Reservation.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            expires_at=timezone.now() - timezone.timedelta(seconds=1),
        )

    @patch("orders.services.reservation_service._stripe_client")
    def test_expiry_closes_open_stripe_session_before_releasing_inventory(
        self, client_factory
    ):
        attempt = PaymentAttempt.objects.create(
            order=self.order,
            checkout_session_id="cs_test_expire_first",
            status=PaymentAttempt.Status.OPEN,
            amount=self.order.grand_total,
            currency="AED",
            expires_at=timezone.now() + timezone.timedelta(minutes=30),
        )
        remote_open = Mock(status="open", payment_status="unpaid")
        remote_expired = Mock(status="expired", payment_status="unpaid")
        client_factory.return_value.v1.checkout.sessions.retrieve.return_value = (
            remote_open
        )
        client_factory.return_value.v1.checkout.sessions.expire.return_value = (
            remote_expired
        )

        self.assertTrue(expire_unpaid_order_if_needed(self.order))
        client_factory.return_value.v1.checkout.sessions.expire.assert_called_once_with(
            "cs_test_expire_first"
        )
        attempt.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(attempt.status, PaymentAttempt.Status.EXPIRED)
        self.assertEqual(self.product.reserved_quantity, 0)

    @patch("orders.services.reservation_service._stripe_client")
    def test_provider_uncertainty_never_releases_unique_inventory(self, client_factory):
        PaymentAttempt.objects.create(
            order=self.order,
            checkout_session_id="cs_test_uncertain",
            status=PaymentAttempt.Status.OPEN,
            amount=self.order.grand_total,
            currency="AED",
            expires_at=timezone.now() + timezone.timedelta(minutes=30),
        )
        client_factory.return_value.v1.checkout.sessions.retrieve.side_effect = (
            RuntimeError("temporary provider outage")
        )

        self.assertFalse(expire_unpaid_order_if_needed(self.order))
        self.product.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.product.reserved_quantity, 1)
        self.assertNotEqual(self.order.status, Order.Status.CANCELLED)

    @patch("orders.services.reservation_service._stripe_client")
    def test_completed_provider_payment_is_not_released(self, client_factory):
        PaymentAttempt.objects.create(
            order=self.order,
            checkout_session_id="cs_test_paid_race",
            status=PaymentAttempt.Status.OPEN,
            amount=self.order.grand_total,
            currency="AED",
            expires_at=timezone.now() + timezone.timedelta(minutes=30),
        )
        client_factory.return_value.v1.checkout.sessions.retrieve.return_value = Mock(
            status="complete", payment_status="paid"
        )
        self.assertFalse(expire_unpaid_order_if_needed(self.order))
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_quantity, 1)

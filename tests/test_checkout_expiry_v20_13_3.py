from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from orders.models import Order, Reservation
from orders.services.inventory_service import reserve
from orders.services.reservation_service import expire_unpaid_order_if_needed

User = get_user_model()


@override_settings(
    STRIPE_ENABLED=True,
    RESERVATION_MINUTES=15,
    STORE_SHIPPING_FEE=Decimal("0.00"),
    STORE_TAX_RATE=Decimal("0.00"),
)
class CheckoutExpiryV20133Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "expiry-customer", password="StrongPass!12345", email="expiry@example.com"
        )
        if hasattr(self.user, "role"):
            self.user.role = "CUSTOMER"
            self.user.save(update_fields=["role"])
        self.category = Category.objects.create(name_ar="مسابيح", name_en="Misbah")
        self.product = Product.objects.create(
            sku="HS-EXP-1",
            name_ar="قطعة اختبار",
            name_en="Expiry Piece",
            category=self.category,
            cost_price=Decimal("10.00"),
            selling_price=Decimal("100.00"),
            available_quantity=1,
            reserved_quantity=0,
            status=Product.Status.AVAILABLE,
        )
        self.order = Order.objects.create(
            reference="HS-EXPIRY-001",
            user=self.user,
            customer_name="Expiry Customer",
            customer_email="expiry@example.com",
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
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )
        self.client.force_login(self.user)

    def test_confirmation_renders_server_backed_countdown(self):
        response = self.client.get(
            reverse("orders:confirmation", args=[self.order.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-checkout-expiry")
        self.assertContains(response, "data-expires-at=")
        self.assertContains(response, "الوقت المتبقي لإكمال الطلب")

    def test_refresh_does_not_extend_reservation(self):
        original = self.reservation.expires_at
        self.client.get(reverse("orders:confirmation", args=[self.order.public_id]))
        self.client.get(reverse("orders:confirmation", args=[self.order.public_id]))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.expires_at, original)

    def test_expired_confirmation_releases_inventory_and_blocks_payment(self):
        self.reservation.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        self.reservation.save(update_fields=["expires_at"])
        response = self.client.get(
            reverse("orders:confirmation", args=[self.order.public_id])
        )
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.reservation.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.product.reserved_quantity, 0)
        self.assertIsNotNone(self.reservation.released_at)
        self.assertContains(response, "انتهت مهلة حجز الطلب")
        self.assertNotContains(
            response,
            reverse("orders:stripe_payment_start", args=[self.order.public_id]),
        )

    @patch("orders.views.create_checkout_session")
    def test_expired_order_cannot_start_new_stripe_session(self, create_session):
        self.reservation.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        self.reservation.save(update_fields=["expires_at"])
        response = self.client.post(
            reverse("orders:stripe_payment_start", args=[self.order.public_id])
        )
        self.assertEqual(response.status_code, 302)
        create_session.assert_not_called()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)

    def test_expired_order_cannot_start_manual_payment(self):
        self.reservation.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        self.reservation.save(update_fields=["expires_at"])
        with override_settings(WHATSAPP_NUMBER="+971504084006"):
            response = self.client.post(
                reverse("orders:manual_payment_start", args=[self.order.public_id])
            )
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)

    def test_service_is_idempotent(self):
        self.reservation.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        self.reservation.save(update_fields=["expires_at"])
        self.assertTrue(expire_unpaid_order_if_needed(self.order))
        self.assertFalse(expire_unpaid_order_if_needed(self.order))
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_quantity, 0)

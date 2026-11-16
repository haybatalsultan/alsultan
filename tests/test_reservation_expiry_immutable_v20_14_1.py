from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import MFADevice, SupervisorPermission, User
from catalog.models import Category, Product
from orders.models import Order, OrderItem, Reservation
from orders.services.stripe_service import create_checkout_session


@override_settings(
    STRIPE_ENABLED=True,
    STRIPE_SECRET_KEY="sk_test_placeholder",
    STRIPE_CHECKOUT_MINUTES=30,
)
class ImmutableReservationExpiryV20141Tests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="cust141", password="StrongPass!12345", role=User.Role.CUSTOMER
        )
        self.owner = User.objects.create_user(
            username="owner141", password="StrongPass!12345", role=User.Role.OWNER
        )
        MFADevice.objects.create(
            user=self.owner, secret="A" * 32, enabled=True, confirmed_at=timezone.now()
        )
        self.category = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="misbah", is_active=True
        )
        self.product = Product.objects.create(
            category=self.category,
            name_ar="اختبار",
            name_en="Test",
            available_quantity=1,
            reserved_quantity=1,
            cost_price="50.00",
            selling_price="100.00",
            status=Product.Status.AVAILABLE,
        )
        self.order = Order.objects.create(
            user=self.customer,
            customer_name="Customer",
            customer_phone="+971501234567",
            currency="AED",
            subtotal="100.00",
            grand_total="100.00",
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            name_ar="اختبار",
            name_en="Test",
            sku=self.product.sku,
            product_reference=self.product.product_reference,
            quantity=1,
            unit_price="100.00",
            line_total="100.00",
        )
        self.reservation = Reservation.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            expires_at=timezone.now() + timezone.timedelta(minutes=8),
        )

    def _login_owner_mfa(self):
        self.client.login(username="owner141", password="StrongPass!12345")
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session["mfa_verified_at"] = timezone.now().timestamp()
        session.save()

    def test_manual_payment_selection_does_not_extend_deadline(self):
        self.assertTrue(
            self.client.login(username="cust141", password="StrongPass!12345")
        )
        original = self.reservation.expires_at
        with (
            patch("orders.views.current_payment_policy") as policy,
            patch(
                "orders.views.whatsapp_url", return_value="https://wa.me/971500000000"
            ),
        ):
            policy.return_value.manual = True
            response = self.client.post(
                reverse("orders:manual_payment_start", args=[self.order.public_id])
            )
        self.assertEqual(response.status_code, 302)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.expires_at, original)

    @patch("orders.services.stripe_service._stripe_client")
    def test_stripe_session_does_not_extend_original_reservation(self, client_factory):
        original = self.reservation.expires_at
        session = Mock(
            id="cs_test_immutable",
            url="https://checkout.stripe.com/c/test",
            status="open",
        )
        client_factory.return_value.v1.checkout.sessions.create.return_value = session
        request = self.client.request().wsgi_request
        request.user = self.customer
        request.META["HTTP_HOST"] = "testserver"
        create_checkout_session(order=self.order, request=request)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.expires_at, original)

    def test_owner_can_extend_active_reservation_by_allowlisted_duration(self):
        self._login_owner_mfa()
        original = self.reservation.expires_at
        response = self.client.post(
            reverse("core:management_order", args=[self.order.public_id]),
            {"action": "extend_reservation", "extend-minutes": "30"},
        )
        self.assertEqual(response.status_code, 302)
        self.reservation.refresh_from_db()
        self.assertEqual(
            self.reservation.expires_at, original + timezone.timedelta(minutes=30)
        )

    def test_supervisor_without_permission_cannot_extend(self):
        supervisor = User.objects.create_user(
            username="sup141", password="StrongPass!12345", role=User.Role.SUPERVISOR
        )
        SupervisorPermission.objects.create(
            user=supervisor, view_orders=True, extend_reservations=False
        )
        MFADevice.objects.create(
            user=supervisor, secret="B" * 32, enabled=True, confirmed_at=timezone.now()
        )
        self.client.login(username="sup141", password="StrongPass!12345")
        session = self.client.session
        session["mfa_verified_user_id"] = str(supervisor.pk)
        session["mfa_verified_at"] = timezone.now().timestamp()
        session.save()
        original = self.reservation.expires_at
        response = self.client.post(
            reverse("core:management_order", args=[self.order.public_id]),
            {"action": "extend_reservation", "extend-minutes": "30"},
        )
        self.assertEqual(response.status_code, 403)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.expires_at, original)

    def test_invalid_extension_value_is_not_accepted(self):
        self._login_owner_mfa()
        original = self.reservation.expires_at
        response = self.client.post(
            reverse("core:management_order", args=[self.order.public_id]),
            {"action": "extend_reservation", "extend-minutes": "999"},
        )
        self.assertEqual(response.status_code, 200)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.expires_at, original)

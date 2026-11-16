from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import SupervisorPermission, User
from catalog.models import Category, Product
from core.models import StoreSetting
from orders.models import Order, PaymentAttempt, Reservation
from orders.services.inventory_service import reserve
from tests.helpers import login_management


class ManagementPaymentWorkflowV2098Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "owner-v2098", password="VeryStrongPass!123", role=User.Role.OWNER
        )
        self.customer = User.objects.create_user(
            "customer-v2098", password="VeryStrongPass!123", role=User.Role.CUSTOMER
        )
        self.category = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="misbah-v2098"
        )
        self.product = Product.objects.create(
            name_ar="مسباح اختبار إدارة",
            name_en="Management Test Misbah",
            category=self.category,
            cost_price=Decimal("100.00"),
            selling_price=Decimal("500.00"),
            available_quantity=1,
            reserved_quantity=0,
            status=Product.Status.AVAILABLE,
        )

    def make_order(self, reference, **kwargs):
        defaults = dict(
            user=self.customer,
            customer_name="Customer",
            customer_email="customer@example.com",
            customer_phone="+971501234567",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("500.00"),
            grand_total=Decimal("500.00"),
            currency="AED",
        )
        defaults.update(kwargs)
        return Order.objects.create(reference=reference, **defaults)

    def reserve_for_order(self, order):
        reserve(self.product.pk, 1, order.reference, self.customer)
        return Reservation.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            expires_at=timezone.now() + timezone.timedelta(minutes=30),
        )

    def test_management_page_renders_persisted_paid_confirmed_state_not_default_choices(
        self,
    ):
        order = self.make_order(
            "HS-MGMT-PAID",
            status=Order.Status.CONFIRMED,
            payment_status=Order.PaymentStatus.PAID,
            payment_method=Order.PaymentMethod.STRIPE,
        )
        PaymentAttempt.objects.create(
            order=order,
            checkout_session_id="cs_test_mgmt_paid",
            status=PaymentAttempt.Status.PAID,
            amount=order.grand_total,
            currency="AED",
        )
        login_management(self.client, self.owner, "VeryStrongPass!123")
        response = self.client.get(
            reverse("core:management_order", args=[order.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paid")
        self.assertContains(response, 'value="CONFIRMED" selected', html=False)
        self.assertContains(response, "Stripe")
        self.assertNotContains(response, 'name="pay-payment_status"')
        self.assertContains(response, 'value="CONFIRMED" selected')

    def test_manual_payment_confirmation_consumes_inventory_once_and_confirms_order(
        self,
    ):
        order = self.make_order(
            "HS-MANUAL-PAID", payment_method=Order.PaymentMethod.MANUAL
        )
        reservation = self.reserve_for_order(order)
        login_management(self.client, self.owner, "VeryStrongPass!123")
        url = reverse("core:management_order", args=[order.public_id])
        payload = {"action": "manual_paid", "manual-confirm_received": "on"}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        reservation.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.payment_method, Order.PaymentMethod.MANUAL)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertIsNotNone(order.manual_paid_at)
        self.assertEqual(order.manual_paid_by, self.owner)
        self.assertIsNotNone(reservation.consumed_at)
        self.assertEqual(self.product.available_quantity, 0)
        self.assertEqual(self.product.reserved_quantity, 0)

        # Replay must not consume stock again or create a negative quantity.
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_quantity, 0)
        self.assertEqual(self.product.reserved_quantity, 0)

    def test_supervisor_without_mark_paid_cannot_confirm_manual_payment(self):
        order = self.make_order(
            "HS-MANUAL-DENY", payment_method=Order.PaymentMethod.MANUAL
        )
        self.reserve_for_order(order)
        supervisor = User.objects.create_user(
            "supervisor-v2098", password="VeryStrongPass!123", role=User.Role.SUPERVISOR
        )
        SupervisorPermission.objects.create(
            user=supervisor, view_orders=True, mark_paid=False
        )
        login_management(self.client, supervisor, "VeryStrongPass!123")
        response = self.client.post(
            reverse("core:management_order", args=[order.public_id]),
            {"action": "manual_paid", "manual-confirm_received": "on"},
        )
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertNotEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.product.available_quantity, 1)

    def test_active_stripe_attempt_blocks_manual_payment_confirmation(self):
        order = self.make_order(
            "HS-MANUAL-BLOCK", payment_method=Order.PaymentMethod.UNSET
        )
        self.reserve_for_order(order)
        PaymentAttempt.objects.create(
            order=order,
            checkout_session_id="cs_test_active_manual_block",
            status=PaymentAttempt.Status.OPEN,
            amount=order.grand_total,
            currency="AED",
        )
        login_management(self.client, self.owner, "VeryStrongPass!123")
        response = self.client.post(
            reverse("core:management_order", args=[order.public_id]),
            {"action": "manual_paid", "manual-confirm_received": "on"},
        )
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertNotEqual(order.payment_status, Order.PaymentStatus.PAID)

    def test_unpaid_order_cannot_jump_into_fulfilment(self):
        order = self.make_order("HS-UNPAID-FULFIL", status=Order.Status.CONFIRMED)
        login_management(self.client, self.owner, "VeryStrongPass!123")
        response = self.client.post(
            reverse("core:management_order", args=[order.public_id]),
            {"action": "status", "order-status": Order.Status.PREPARING},
        )
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)

    def test_unpaid_order_cannot_change_shipping_details(self):
        order = self.make_order("HS-UNPAID-SHIP", status=Order.Status.CONFIRMED)
        login_management(self.client, self.owner, "VeryStrongPass!123")
        response = self.client.post(
            reverse("core:management_order", args=[order.public_id]),
            {
                "action": "shipping",
                "ship-shipping_carrier": "Aramex",
                "ship-tracking_number": "ABC123",
                "ship-tracking_url": "https://example.com/track/ABC123",
            },
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(STRIPE_ENABLED=True)
    def test_manual_payment_selection_requires_post_and_records_method(self):
        StoreSetting.objects.create(
            singleton=True, online_payment_enabled=True, whatsapp_checkout_enabled=True
        )
        order = self.make_order("HS-MANUAL-SELECT")
        # v20.13.3+: payment-method selection is only valid while the
        # server-authoritative checkout reservation is still active.
        self.reserve_for_order(order)
        self.client.force_login(self.customer)
        url = reverse("orders:manual_payment_start", args=[order.public_id])
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.payment_method, Order.PaymentMethod.MANUAL)

    def test_dashboard_distinguishes_available_and_sold_out_products(self):
        sold = Product.objects.create(
            name_ar="مباع",
            name_en="Sold",
            category=self.category,
            cost_price=Decimal("10.00"),
            selling_price=Decimal("20.00"),
            available_quantity=0,
            reserved_quantity=0,
            status=Product.Status.SOLD,
        )
        login_management(self.client, self.owner, "VeryStrongPass!123")
        response = self.client.get(reverse("core:management_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["available_products"], 1)
        self.assertEqual(response.context["sold_out_products"], 1)
        self.assertContains(response, "نفد المخزون")
        self.assertTrue(sold.pk)


class ManagementCancellationInventoryV2098Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "owner-cancel-v2098", password="VeryStrongPass!123", role=User.Role.OWNER
        )
        self.customer = User.objects.create_user(
            "customer-cancel-v2098",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )
        self.category = Category.objects.create(
            name_ar="مسابيح إلغاء", name_en="Cancel Misbah", slug="cancel-misbah-v2098"
        )
        self.product = Product.objects.create(
            name_ar="مسباح إلغاء",
            name_en="Cancel Test",
            category=self.category,
            cost_price=Decimal("100.00"),
            selling_price=Decimal("500.00"),
            available_quantity=1,
            reserved_quantity=0,
            status=Product.Status.AVAILABLE,
        )

    def _reserved_order(self, *, paid=False):
        order = Order.objects.create(
            reference="HS-CANCEL-PAID" if paid else "HS-CANCEL-UNPAID",
            user=self.customer,
            customer_name="Customer",
            customer_phone="+971501234567",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("500.00"),
            grand_total=Decimal("500.00"),
            payment_status=Order.PaymentStatus.PAID
            if paid
            else Order.PaymentStatus.UNPAID,
            status=Order.Status.CONFIRMED if paid else Order.Status.PENDING,
            payment_method=Order.PaymentMethod.MANUAL,
        )
        reserve(self.product.pk, 1, order.reference, self.customer)
        reservation = Reservation.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            expires_at=timezone.now() + timezone.timedelta(minutes=30),
        )
        return order, reservation

    def test_unpaid_cancellation_releases_inventory(self):
        order, reservation = self._reserved_order(paid=False)
        login_management(self.client, self.owner, "VeryStrongPass!123")
        response = self.client.post(
            reverse("core:management_order", args=[order.public_id]),
            {"action": "status", "order-status": Order.Status.CANCELLED},
        )
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        reservation.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertIsNotNone(reservation.released_at)
        self.assertEqual(self.product.reserved_quantity, 0)
        self.assertEqual(self.product.available_quantity, 1)

    def test_paid_order_cannot_be_cancelled_without_refund_workflow(self):
        order, reservation = self._reserved_order(paid=True)
        login_management(self.client, self.owner, "VeryStrongPass!123")
        response = self.client.post(
            reverse("core:management_order", args=[order.public_id]),
            {"action": "status", "order-status": Order.Status.CANCELLED},
        )
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        reservation.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertIsNone(reservation.released_at)

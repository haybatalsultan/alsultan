from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import SupervisorPermission, User
from catalog.models import Category, Product
from orders.models import Order, OrderItem
from orders.services.loyalty_service import loyalty_status_for_user
from orders.services.risk_service import customer_risk_signals
from tests.helpers import login_management


class V207Base(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name_ar="مسابيح",
            name_en="Misbah",
            slug="misbah-v207",
        )
        self.product = Product.objects.create(
            name_ar="مسباح اختبار",
            name_en="Test Misbah",
            category=self.category,
            cost_price=Decimal("400.00"),
            selling_price=Decimal("1000.00"),
            available_quantity=10,
            status=Product.Status.AVAILABLE,
        )
        self.customer = User.objects.create_user(
            username="customer-v207",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
            email="customer-v207@example.com",
        )

    def make_order(
        self,
        *,
        reference,
        user=None,
        status=Order.Status.PENDING,
        payment_status=Order.PaymentStatus.UNPAID,
        delivered_at=None,
        grand_total=Decimal("1000.00"),
        with_item=False,
        item_cost=Decimal("400.00"),
    ):
        order = Order.objects.create(
            reference=reference,
            user=user or self.customer,
            customer_name="Customer",
            customer_email="customer-v207@example.com",
            customer_phone="+971501234567",
            country="AE",
            area="Abu Dhabi",
            subtotal=grand_total,
            grand_total=grand_total,
            status=status,
            payment_status=payment_status,
            delivered_at=delivered_at,
        )
        if with_item:
            OrderItem.objects.create(
                order=order,
                product=self.product,
                product_reference=self.product.product_reference,
                sku=self.product.sku,
                name_ar=self.product.name_ar,
                name_en=self.product.name_en,
                base_unit_price=grand_total,
                unit_price=grand_total,
                quantity=1,
                line_total=grand_total,
                cost_unit_snapshot=item_cost,
                cost_total_snapshot=item_cost,
            )
        return order


class LoyaltySecurityTests(V207Base):
    def test_loyalty_uses_delivered_orders_only(self):
        self.make_order(reference="HS-L1-PENDING")
        self.assertEqual(loyalty_status_for_user(self.customer).code, "MEMBER")

        self.make_order(
            reference="HS-L1-DELIVERED",
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.PAID,
            delivered_at=timezone.now(),
        )
        status = loyalty_status_for_user(self.customer)
        self.assertEqual(status.code, "NEW")
        self.assertEqual(status.eligible_orders, 1)

    def test_loyalty_progresses_through_new_silver_gold_platinum_royal(self):
        expected_by_count = {
            1: "NEW",
            2: "SILVER",
            3: "SILVER",
            4: "GOLD",
            5: "GOLD",
            6: "GOLD",
            7: "PLATINUM",
            8: "PLATINUM",
            9: "PLATINUM",
            10: "ROYAL",
            11: "ROYAL",
        }
        for idx in range(1, 12):
            self.make_order(
                reference=f"HS-LOYALTY-{idx}",
                status=Order.Status.DELIVERED,
                payment_status=Order.PaymentStatus.PAID,
                delivered_at=timezone.now(),
            )
            self.assertEqual(
                loyalty_status_for_user(self.customer).code,
                expected_by_count[idx],
            )

    def test_refunded_or_returned_orders_do_not_increase_loyalty(self):
        self.make_order(
            reference="HS-REFUNDED",
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.REFUNDED,
            delivered_at=timezone.now(),
        )
        self.make_order(
            reference="HS-RETURNED",
            status=Order.Status.RETURNED,
            payment_status=Order.PaymentStatus.PAID,
            delivered_at=timezone.now(),
        )
        self.assertEqual(loyalty_status_for_user(self.customer).eligible_orders, 0)

    def test_customer_cannot_submit_a_loyalty_tier_field(self):
        self.client.login(
            username="customer-v207",
            password="VeryStrongPass!123",
        )
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "loyalty_tier": "ROYAL",
                "label": "Home",
                "country": "AE",
                "area": "Abu Dhabi",
                "is_default": "on",
            },
        )
        # Whether the address form accepts the partial payload is irrelevant:
        # no writable loyalty field exists and the tier remains derived.
        self.assertNotEqual(loyalty_status_for_user(self.customer).code, "ROYAL")


class FinancialSnapshotTests(V207Base):
    def test_cost_snapshot_does_not_change_when_product_cost_changes(self):
        order = self.make_order(
            reference="HS-COST-1",
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.PAID,
            delivered_at=timezone.now(),
            with_item=True,
        )
        item = order.items.get()
        self.product.cost_price = Decimal("900.00")
        self.product.save(update_fields=["cost_price", "updated_at"])
        item.refresh_from_db()
        self.assertEqual(item.cost_unit_snapshot, Decimal("400.00"))
        self.assertEqual(item.cost_total_snapshot, Decimal("400.00"))

    def test_financial_snapshot_is_immutable(self):
        order = self.make_order(
            reference="HS-COST-2",
            with_item=True,
        )
        item = order.items.get()
        item.cost_total_snapshot = Decimal("1.00")
        with self.assertRaises(RuntimeError):
            item.save()
        with self.assertRaises(RuntimeError):
            OrderItem.objects.filter(pk=item.pk).update(
                cost_total_snapshot=Decimal("1.00")
            )


class SmartAccountantAccessTests(V207Base):
    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_user(
            username="owner-accountant-v207",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )

    def test_smart_accountant_is_owner_only(self):
        supervisor = User.objects.create_user(
            username="supervisor-accountant-v207",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        SupervisorPermission.objects.create(
            user=supervisor,
            view_reports=True,
            export_reports=True,
        )
        login_management(self.client, supervisor, "VeryStrongPass!123")
        response = self.client.get(reverse("core:management_smart_accountant"))
        self.assertEqual(response.status_code, 403)

    def test_owner_can_open_smart_accountant(self):
        login_management(self.client, self.owner, "VeryStrongPass!123")
        response = self.client.get(reverse("core:management_smart_accountant"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "المحاسب الذكي")

    def test_accountant_uses_snapshot_cost_not_current_product_cost(self):
        self.make_order(
            reference="HS-ACCOUNTANT-1",
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.PAID,
            delivered_at=timezone.now(),
            grand_total=Decimal("1000.00"),
            with_item=True,
            item_cost=Decimal("400.00"),
        )
        self.product.cost_price = Decimal("950.00")
        self.product.save(update_fields=["cost_price", "updated_at"])

        login_management(self.client, self.owner, "VeryStrongPass!123")
        response = self.client.get(
            reverse("core:management_smart_accountant"),
            {"period": "today"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cost"], Decimal("400.00"))
        self.assertEqual(response.context["profit"], Decimal("600.00"))

    def test_accountant_loyalty_distribution_uses_new_tiers(self):
        customers = []
        for idx, delivered_count in enumerate((0, 1, 2, 4, 7, 10), start=1):
            customer = User.objects.create_user(
                username=f"tier-customer-{idx}",
                password="VeryStrongPass!123",
                role=User.Role.CUSTOMER,
                email=f"tier-{idx}@example.com",
            )
            customers.append(customer)
            for order_idx in range(delivered_count):
                self.make_order(
                    reference=f"HS-TIER-{idx}-{order_idx}",
                    user=customer,
                    status=Order.Status.DELIVERED,
                    payment_status=Order.PaymentStatus.PAID,
                    delivered_at=timezone.now(),
                )

        login_management(self.client, self.owner, "VeryStrongPass!123")
        response = self.client.get(reverse("core:management_smart_accountant"))
        self.assertEqual(response.status_code, 200)
        counts = response.context["loyalty_counts"]

        # setUp() also creates self.customer with zero qualifying orders.
        self.assertGreaterEqual(counts["member"], 2)
        self.assertEqual(counts["new"], 1)
        self.assertEqual(counts["silver"], 1)
        self.assertEqual(counts["gold"], 1)
        self.assertEqual(counts["platinum"], 1)
        self.assertEqual(counts["royal"], 1)

    def test_custom_period_is_bounded_and_invalid_input_does_not_error(self):
        login_management(self.client, self.owner, "VeryStrongPass!123")
        response = self.client.get(
            reverse("core:management_smart_accountant"),
            {"period": "custom", "start": "not-a-date", "end": "<script>"},
        )
        self.assertEqual(response.status_code, 200)


class DeliveryMilestoneTests(V207Base):
    def test_delivery_transition_records_server_timestamp(self):
        supervisor = User.objects.create_user(
            username="delivery-supervisor-v207",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        SupervisorPermission.objects.create(
            user=supervisor,
            view_orders=True,
            ship_orders=True,
        )
        order = self.make_order(
            reference="HS-DELIVERY-TIME",
            status=Order.Status.SHIPPED,
            payment_status=Order.PaymentStatus.PAID,
        )
        self.assertIsNone(order.delivered_at)

        login_management(self.client, supervisor, "VeryStrongPass!123")
        response = self.client.post(
            reverse("core:management_order", args=[order.public_id]),
            {
                "action": "status",
                "order-status": Order.Status.DELIVERED,
            },
        )
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)
        self.assertIsNotNone(order.delivered_at)


class PaymentWorkflowSecurityTests(V207Base):
    def test_supervisor_with_pending_permission_cannot_refund_paid_order(self):
        supervisor = User.objects.create_user(
            username="payment-supervisor-v207",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        SupervisorPermission.objects.create(
            user=supervisor,
            view_orders=True,
            mark_payment_pending=True,
            mark_paid=False,
        )
        order = self.make_order(
            reference="HS-PAYMENT-1",
            payment_status=Order.PaymentStatus.PAID,
        )
        login_management(self.client, supervisor, "VeryStrongPass!123")
        response = self.client.post(
            reverse("core:management_order", args=[order.public_id]),
            {
                "action": "payment",
                "pay-payment_status": Order.PaymentStatus.REFUNDED,
            },
        )
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)


class RiskSignalTests(V207Base):
    def test_repeated_cancellations_generate_review_signal_without_blocking_customer(
        self,
    ):
        for idx in range(3):
            self.make_order(
                reference=f"HS-RISK-{idx}",
                status=Order.Status.CANCELLED,
            )
        signals = customer_risk_signals(days=30)
        codes = {
            signal.code
            for signal in signals
            if signal.customer_id == str(self.customer.public_id)
        }
        self.assertIn("HIGH_CANCELLATION_RATE", codes)

        self.customer.refresh_from_db()
        self.assertTrue(self.customer.is_active)
        self.assertFalse(self.customer.is_archived)

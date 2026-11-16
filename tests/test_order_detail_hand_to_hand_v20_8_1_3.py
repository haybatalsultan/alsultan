from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import SupervisorPermission, User
from catalog.models import Category, Product
from core.models import AuditLog
from orders.models import Order, OrderTimelineEvent
from tests.helpers import login_management


class OrderDetailHandToHandV20813Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="handover-owner",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        self.supervisor = User.objects.create_user(
            username="handover-supervisor",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        SupervisorPermission.objects.create(
            user=self.supervisor,
            view_orders=True,
            ship_orders=True,
            view_order_timeline=True,
        )
        self.order = Order.objects.create(
            reference="HS-HANDOVER-001",
            customer_name="Direct Buyer",
            customer_phone="+971501234567",
            country="AE",
            area="Direct Sale",
            subtotal=Decimal("1500.00"),
            grand_total=Decimal("1500.00"),
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.UNPAID,
            payment_method=Order.PaymentMethod.DEFERRED,
            sale_channel=Order.SaleChannel.DIRECT,
            payment_due_date=timezone.localdate(),
            delivered_at=timezone.now(),
        )
        login_management(self.client, self.owner, "VeryStrongPass!123")

    def test_deferred_order_detail_shows_due_balance_and_record_payment(self):
        response = self.client.get(
            reverse("core:management_order", args=[self.order.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تاريخ الاستحقاق")
        self.assertContains(response, "تسجيل دفعة")
        self.assertEqual(response.context["deferred_paid"], 0)
        self.assertEqual(response.context["deferred_outstanding"], Decimal("1500.00"))

    def test_hand_to_hand_can_be_recorded_for_deferred_direct_sale(self):
        response = self.client.post(
            reverse("core:management_order", args=[self.order.public_id]),
            {
                "action": "hand_to_hand",
                "handover-confirm_handover": "on",
                "handover-note": "تم التسليم مباشرة",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.delivery_method,
            Order.DeliveryMethod.HAND_TO_HAND,
        )
        self.assertIsNotNone(self.order.hand_to_hand_at)
        self.assertEqual(self.order.hand_to_hand_by, self.owner)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.UNPAID)
        self.assertTrue(
            OrderTimelineEvent.objects.filter(
                order=self.order,
                label_en="Item handed directly to the buyer",
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action="order_hand_to_hand_delivered",
                object_reference=self.order.reference,
            ).exists()
        )

    def test_hand_to_hand_cannot_be_recorded_without_confirmation(self):
        response = self.client.post(
            reverse("core:management_order", args=[self.order.public_id]),
            {"action": "hand_to_hand"},
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertIsNone(self.order.hand_to_hand_at)

    def test_unpaid_non_deferred_order_cannot_be_handed_over(self):
        self.order.payment_method = Order.PaymentMethod.MANUAL
        self.order.save(update_fields=["payment_method", "updated_at"])
        response = self.client.post(
            reverse("core:management_order", args=[self.order.public_id]),
            {
                "action": "hand_to_hand",
                "handover-confirm_handover": "on",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.order.refresh_from_db()
        self.assertIsNone(self.order.hand_to_hand_at)

    def test_order_detail_uses_haybat_order_tracker(self):
        OrderTimelineEvent.objects.create(
            order=self.order,
            kind=OrderTimelineEvent.Kind.ORDER_CREATED,
            label_ar="اختبار",
            label_en="Test",
            actor=self.owner,
        )
        response = self.client.get(
            reverse("core:management_order", args=[self.order.public_id])
        )
        self.assertContains(response, "haybat-order-tracker")


class QuickSaleHandToHandSnapshotV20813Tests(TestCase):
    def test_direct_sale_model_has_hand_to_hand_delivery_choice(self):
        self.assertIn(
            ("HAND_TO_HAND", "Hand-to-hand"),
            Order.DeliveryMethod.choices,
        )

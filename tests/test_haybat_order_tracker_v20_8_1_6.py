from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from orders.models import Order, OrderTimelineEvent
from tests.helpers import login_management


class HaybatOrderTrackerV20816Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="tracker-owner",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        login_management(self.client, self.owner, "VeryStrongPass!123")

    def make_order(self, **overrides):
        data = {
            "reference": "HS-TRACK-001",
            "customer_name": "Buyer",
            "customer_phone": "+971501234567",
            "country": "AE",
            "area": "Abu Dhabi",
            "subtotal": Decimal("1500.00"),
            "grand_total": Decimal("1500.00"),
            "status": Order.Status.SHIPPED,
            "payment_status": Order.PaymentStatus.PAID,
            "payment_method": Order.PaymentMethod.CASH,
        }
        data.update(overrides)
        return Order.objects.create(**data)

    def test_shipping_order_uses_four_stage_haybat_tracker(self):
        order = self.make_order()
        response = self.client.get(reverse("core:management_order", args=[order.public_id]))
        self.assertEqual(response.status_code, 200)
        for label in ("تم الطلب", "التجهيز", "جاري التوصيل", "تم التسليم"):
            self.assertContains(response, label)
        self.assertContains(response, "haybat-order-tracker")

    def test_hand_to_hand_order_uses_direct_sale_stages(self):
        order = self.make_order(
            reference="HS-TRACK-HAND",
            sale_channel=Order.SaleChannel.DIRECT,
            delivery_method=Order.DeliveryMethod.HAND_TO_HAND,
            hand_to_hand_at=timezone.now(),
            hand_to_hand_by=self.owner,
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.UNPAID,
            payment_method=Order.PaymentMethod.DEFERRED,
            payment_due_date=timezone.localdate(),
        )
        response = self.client.get(reverse("core:management_order", args=[order.public_id]))
        self.assertContains(response, "تم تسجيل البيع")
        self.assertContains(response, "الدفع")
        self.assertContains(response, "استلام يدًا بيد")
        self.assertContains(response, "مؤجل")
        self.assertNotContains(response, "جاري التوصيل")

    def test_raw_delivered_status_is_not_shown_in_detailed_activity(self):
        order = self.make_order(reference="HS-TRACK-DEL", status=Order.Status.DELIVERED)
        OrderTimelineEvent.objects.create(
            order=order,
            kind=OrderTimelineEvent.Kind.STATUS_CHANGED,
            label_ar="تم تحديث حالة الطلب",
            label_en="Order status updated",
            actor=self.owner,
            from_value=Order.Status.SHIPPED,
            to_value=Order.Status.DELIVERED,
        )
        response = self.client.get(reverse("core:management_order", args=[order.public_id]))
        self.assertContains(response, "حالة الطلب: تم التسليم")
        self.assertNotContains(response, "SHIPPED → DELIVERED")

    def test_tracker_is_server_derived_and_has_no_client_state_inputs(self):
        order = self.make_order(reference="HS-TRACK-SERVER")
        response = self.client.get(reverse("core:management_order", args=[order.public_id]))
        self.assertNotContains(response, 'name="tracking_stage"')

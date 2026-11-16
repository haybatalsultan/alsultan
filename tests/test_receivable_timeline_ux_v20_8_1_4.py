from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from orders.models import DirectPaymentEntry, Order, OrderTimelineEvent
from tests.helpers import login_management


class ReceivableTimelineUXV20814Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="receivable-ux-owner",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        self.order = Order.objects.create(
            reference="HS-REC-UX-001",
            customer_name="Direct Customer",
            customer_phone="+971501234567",
            country="AE",
            area="Direct Sale",
            subtotal=Decimal("2571.25"),
            grand_total=Decimal("2571.25"),
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.UNPAID,
            payment_method=Order.PaymentMethod.DEFERRED,
            sale_channel=Order.SaleChannel.DIRECT,
            payment_due_date=timezone.localdate(),
            delivered_at=timezone.now(),
        )
        login_management(self.client, self.owner, "VeryStrongPass!123")

    def payment_url(self):
        return reverse("core:management_receivable_payment", args=[self.order.public_id])

    def test_arabic_receivable_page_is_fully_localized(self):
        response = self.client.get(self.payment_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "مبلغ الدفعة")
        self.assertContains(response, "طريقة الدفع")
        self.assertContains(response, "ملاحظة")
        self.assertContains(response, "عميل مباشر")
        self.assertContains(response, "سداد كامل المتبقي")

    def test_payment_requires_explicit_received_confirmation(self):
        response = self.client.post(
            self.payment_url(),
            {
                "amount": "100.00",
                "payment_method": Order.PaymentMethod.CASH,
                "note": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(DirectPaymentEntry.objects.filter(order=self.order).exists())

    def test_valid_partial_payment_uses_prg_and_preserves_balance(self):
        response = self.client.post(
            self.payment_url(),
            {
                "amount": "500.00",
                "payment_method": Order.PaymentMethod.CASH,
                "note": "received",
                "confirm_received": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PARTIALLY_PAID)
        self.assertEqual(
            self.order.direct_payments.aggregate(
                total=__import__("django.db.models", fromlist=["Sum"]).Sum("amount")
            )["total"],
            Decimal("500.00"),
        )

    def test_overpayment_is_rejected_server_side(self):
        response = self.client.post(
            self.payment_url(),
            {
                "amount": "3000.00",
                "payment_method": Order.PaymentMethod.CASH,
                "confirm_received": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(DirectPaymentEntry.objects.filter(order=self.order).exists())

    def test_order_timeline_hides_noop_transition(self):
        OrderTimelineEvent.objects.create(
            order=self.order,
            kind=OrderTimelineEvent.Kind.PAYMENT_CHANGED,
            label_ar="تم تسجيل البيع كدفعة مؤجلة",
            label_en="Direct sale recorded as deferred payment",
            actor=self.owner,
            from_value=Order.PaymentStatus.UNPAID,
            to_value=Order.PaymentStatus.UNPAID,
        )
        response = self.client.get(
            reverse("core:management_order", args=[self.order.public_id])
        )
        self.assertContains(response, "طريقة الدفع")
        self.assertNotContains(response, "UNPAID → UNPAID")

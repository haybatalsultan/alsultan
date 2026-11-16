from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.utils import timezone

from accounts.models import User
from orders.models import DirectPaymentEntry, Order
from orders.services.accountant_service import build_accountant_report


class DeferredAccountantImportRegressionTests(TestCase):
    def test_accountant_report_handles_direct_payment_entries(self):
        owner = User.objects.create_user(
            username="accountant-import-owner",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        order = Order.objects.create(
            reference="HS-DEFERRED-IMPORT-1",
            customer_name="Deferred Buyer",
            customer_phone="+971501234567",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("1000.00"),
            grand_total=Decimal("1000.00"),
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.PARTIALLY_PAID,
            payment_method=Order.PaymentMethod.DEFERRED,
            delivered_at=timezone.now(),
            payment_due_date=timezone.localdate(),
        )
        DirectPaymentEntry.objects.create(
            order=order,
            amount=Decimal("250.00"),
            payment_method=Order.PaymentMethod.CASH,
            received_by=owner,
        )
        DirectPaymentEntry.objects.create(
            order=order,
            amount=Decimal("100.00"),
            payment_method=Order.PaymentMethod.BANK_TRANSFER,
            received_by=owner,
        )

        request = RequestFactory().get("/", {"period": "today"})
        request.user = owner
        report = build_accountant_report(request)

        self.assertIn("outstanding", report)
        self.assertEqual(report["outstanding"], Decimal("650.00"))

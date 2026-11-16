from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from orders.models import Order
from tests.helpers import login_management


class InvoicePaymentGuardV20834Tests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user(username="invoice-guard-owner",password="VeryStrongPass!123",role=User.Role.OWNER)
        self.order=Order.objects.create(reference="INV-GUARD-1",customer_name="Test",customer_phone="+971500000000",subtotal=Decimal("100"),grand_total=Decimal("100"),payment_status=Order.PaymentStatus.UNPAID,status=Order.Status.PENDING)
        login_management(self.client,self.owner,"VeryStrongPass!123")

    def test_order_journey_hides_invoice_actions_while_unpaid(self):
        response=self.client.get(reverse("core:management_order",args=[self.order.public_id]))
        self.assertNotContains(response,"عرض الفاتورة")
        self.assertNotContains(response,"إنشاء فاتورة")
        self.assertNotContains(response,">PDF<")

    def test_order_journey_allows_invoice_action_only_after_paid(self):
        self.order.payment_status=Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status","updated_at"])
        response=self.client.get(reverse("core:management_order",args=[self.order.public_id]))
        self.assertContains(response,"إنشاء فاتورة")

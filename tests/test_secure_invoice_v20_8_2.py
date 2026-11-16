from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import SupervisorPermission, User
from core.models import AuditLog
from orders.models import DirectPaymentEntry, Invoice, InvoiceItem, Order, OrderItem
from tests.helpers import login_management


class SecureInvoiceV2082Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="invoice-owner",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        self.supervisor = User.objects.create_user(
            username="invoice-supervisor",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        SupervisorPermission.objects.create(
            user=self.supervisor,
            view_orders=True,
        )
        self.customer = User.objects.create_user(
            username="invoice-customer",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )
        self.order = Order.objects.create(
            reference="HS-INVOICE-001",
            customer_name="Invoice Buyer",
            customer_phone="+971501234567",
            customer_email="buyer@example.com",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("1500.00"),
            discount_total=Decimal("100.00"),
            tax_total=Decimal("0.00"),
            shipping_total=Decimal("0.00"),
            grand_total=Decimal("1400.00"),
            currency="AED",
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.PARTIALLY_PAID,
            payment_method=Order.PaymentMethod.DEFERRED,
            sale_channel=Order.SaleChannel.DIRECT,
            delivery_method=Order.DeliveryMethod.HAND_TO_HAND,
            payment_due_date=timezone.localdate() + timedelta(days=20),
            delivered_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=self.order,
            product_reference="HSP-INVOICE-001",
            sku="HS00050",
            name_ar="مسباح يسر كلاسيكي ثقيل",
            name_en="Classic Heavy Yusr Misbah",
            base_unit_price=Decimal("1500.00"),
            unit_price=Decimal("1500.00"),
            discount=Decimal("100.00"),
            tax=Decimal("0.00"),
            quantity=1,
            line_total=Decimal("1400.00"),
            cost_unit_snapshot=Decimal("600.00"),
            cost_total_snapshot=Decimal("600.00"),
        )
        DirectPaymentEntry.objects.create(
            order=self.order,
            amount=Decimal("500.00"),
            payment_method=Order.PaymentMethod.CASH,
            received_by=self.owner,
        )
        login_management(self.client, self.owner, "VeryStrongPass!123")

    def create_invoice(self):
        return self.client.post(
            reverse("core:management_invoice_create", args=[self.order.public_id])
        )

    def test_owner_creates_one_immutable_snapshot(self):
        response = self.create_invoice()
        self.assertEqual(response.status_code, 302)
        invoice = Invoice.objects.get(order=self.order)
        self.assertRegex(invoice.invoice_number, r"^INV-\d{4}-\d{6,}$")
        self.assertEqual(invoice.grand_total_snapshot, Decimal("1400.00"))
        self.assertEqual(invoice.paid_total_snapshot, Decimal("500.00"))
        self.assertEqual(invoice.outstanding_snapshot, Decimal("900.00"))
        self.assertEqual(invoice.items.get().sku_snapshot, "HS00050")
        self.assertTrue(
            AuditLog.objects.filter(action="invoice_created").exists()
        )

    def test_repeated_create_is_idempotent(self):
        self.create_invoice()
        self.create_invoice()
        self.assertEqual(Invoice.objects.filter(order=self.order).count(), 1)

    def test_snapshot_does_not_change_when_order_changes(self):
        self.create_invoice()
        invoice = Invoice.objects.get(order=self.order)
        self.order.grand_total = Decimal("9999.00")
        self.order.save(update_fields=["grand_total", "updated_at"])
        invoice.refresh_from_db()
        self.assertEqual(invoice.grand_total_snapshot, Decimal("1400.00"))

    def test_invoice_and_items_reject_orm_updates_and_deletes(self):
        self.create_invoice()
        invoice = Invoice.objects.get(order=self.order)
        item = invoice.items.get()
        with self.assertRaises(RuntimeError):
            Invoice.objects.filter(pk=invoice.pk).update(grand_total_snapshot=1)
        with self.assertRaises(RuntimeError):
            InvoiceItem.objects.filter(pk=item.pk).update(line_total_snapshot=1)
        with self.assertRaises(RuntimeError):
            invoice.delete()
        with self.assertRaises(RuntimeError):
            item.delete()

    def test_invoice_never_snapshots_owner_cost(self):
        self.create_invoice()
        invoice = Invoice.objects.get(order=self.order)
        field_names = {field.name for field in InvoiceItem._meta.fields}
        self.assertNotIn("cost_unit_snapshot", field_names)
        self.assertNotIn("cost_total_snapshot", field_names)
        response = self.client.get(
            reverse("core:management_invoice", args=[invoice.public_id])
        )
        self.assertNotContains(response, "600.00")

    def test_pdf_is_real_pdf_and_private(self):
        self.create_invoice()
        invoice = Invoice.objects.get(order=self.order)
        response = self.client.get(
            reverse("core:management_invoice_pdf", args=[invoice.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertGreater(len(response.content), 1000)
        self.assertTrue(
            AuditLog.objects.filter(action="invoice_pdf_generated").exists()
        )

    def test_supervisor_with_view_orders_can_view_existing_invoice(self):
        self.create_invoice()
        invoice = Invoice.objects.get(order=self.order)
        self.client.logout()
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        response = self.client.get(
            reverse("core:management_invoice", args=[invoice.public_id])
        )
        self.assertEqual(response.status_code, 200)

    def test_supervisor_cannot_create_invoice(self):
        self.client.logout()
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        response = self.client.post(
            reverse("core:management_invoice_create", args=[self.order.public_id])
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Invoice.objects.exists())

    def test_customer_cannot_access_management_invoice(self):
        self.create_invoice()
        invoice = Invoice.objects.get(order=self.order)
        self.client.logout()
        self.client.login(
            username="invoice-customer",
            password="VeryStrongPass!123",
        )
        response = self.client.get(
            reverse("core:management_invoice", args=[invoice.public_id])
        )
        self.assertIn(response.status_code, {302, 403})

    def test_cancelled_order_cannot_be_invoiced(self):
        self.order.status = Order.Status.CANCELLED
        self.order.save(update_fields=["status", "updated_at"])
        response = self.create_invoice()
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Invoice.objects.exists())

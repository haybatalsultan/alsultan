from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from core.models import StoreSetting
from orders.models import Invoice, Order
from tests.helpers import login_management


class PremiumInvoiceSettingsV20821Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="invoice-settings-owner",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        self.supervisor = User.objects.create_user(
            username="invoice-settings-super",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        login_management(self.client, self.owner, "VeryStrongPass!123")

    def test_owner_can_update_branding_but_not_financial_snapshot_fields(self):
        StoreSetting.objects.get_or_create(singleton=True)
        response = self.client.post(
            reverse("core:management_invoice_settings"),
            {
                "invoice_language": "ar",
                "invoice_business_name": "هيبة السلطان",
                "invoice_phone": "+971 50 408 4006",
                "invoice_email": "info@haybatalsultan.com",
                "invoice_address": "أبوظبي، الإمارات العربية المتحدة",
                "invoice_thank_you": "شكرًا لاختياركم هيبة السلطان",
                "invoice_footer_note": "فاتورة إلكترونية",
                "invoice_stamp_mode": "PAID",
                "invoice_show_phone": "on",
                "invoice_show_email": "on",
                "invoice_show_order_reference": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        setting = StoreSetting.objects.get(singleton=True)
        self.assertEqual(setting.invoice_language, "ar")
        self.assertEqual(setting.invoice_stamp_mode, "PAID")
        response = self.client.get(reverse("core:management_invoice_settings"))
        self.assertNotContains(response, 'name="grand_total_snapshot"')
        self.assertNotContains(response, 'name="paid_total_snapshot"')
        self.assertNotContains(response, 'name="invoice_number"')

    def test_supervisor_cannot_open_or_change_invoice_settings(self):
        self.client.logout()
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        self.assertEqual(
            self.client.get(reverse("core:management_invoice_settings")).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(reverse("core:management_invoice_settings"), {}).status_code,
            403,
        )

    def test_paid_unset_method_is_presented_as_confirmed_not_not_selected(self):
        setting, _ = StoreSetting.objects.get_or_create(singleton=True)
        order = Order.objects.create(
            reference="HS-PREMIUM-INVOICE",
            customer_name="Buyer",
            customer_phone="+971501234567",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("100.00"),
            grand_total=Decimal("100.00"),
            payment_status=Order.PaymentStatus.PAID,
            payment_method=Order.PaymentMethod.UNSET,
            status=Order.Status.DELIVERED,
        )
        invoice = Invoice.objects.create(
            order=order,
            invoice_number="INV-2026-999999",
            issued_by=self.owner,
            order_reference_snapshot=order.reference,
            customer_name_snapshot="Buyer",
            customer_phone_snapshot=order.customer_phone,
            currency_snapshot="AED",
            subtotal_snapshot=Decimal("100.00"),
            discount_total_snapshot=Decimal("0.00"),
            tax_total_snapshot=Decimal("0.00"),
            shipping_total_snapshot=Decimal("0.00"),
            grand_total_snapshot=Decimal("100.00"),
            paid_total_snapshot=Decimal("100.00"),
            outstanding_snapshot=Decimal("0.00"),
            payment_status_snapshot=Order.PaymentStatus.PAID,
            payment_method_snapshot=Order.PaymentMethod.UNSET,
            delivery_method_snapshot=Order.DeliveryMethod.HAND_TO_HAND,
        )
        response = self.client.get(
            reverse("core:management_invoice", args=[invoice.public_id])
        )
        self.assertContains(response, "مدفوع / مؤكد")
        self.assertNotContains(response, "لم يتم الاختيار")

    def test_stamp_paid_only_rule_does_not_show_stamp_for_unpaid_invoice(self):
        setting, _ = StoreSetting.objects.get_or_create(singleton=True)
        setting.invoice_stamp_url = "https://res.cloudinary.com/demo/image/upload/stamp.png"
        setting.invoice_stamp_mode = "PAID"
        setting.save(update_fields=["invoice_stamp_url", "invoice_stamp_mode", "updated_at"])
        order = Order.objects.create(
            reference="HS-UNPAID-INVOICE",
            customer_name="Buyer",
            customer_phone="+971501234567",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("100.00"),
            grand_total=Decimal("100.00"),
            payment_status=Order.PaymentStatus.UNPAID,
            status=Order.Status.PENDING,
        )
        invoice = Invoice.objects.create(
            order=order,
            invoice_number="INV-2026-999998",
            issued_by=self.owner,
            order_reference_snapshot=order.reference,
            customer_name_snapshot="Buyer",
            customer_phone_snapshot=order.customer_phone,
            currency_snapshot="AED",
            subtotal_snapshot=Decimal("100.00"),
            discount_total_snapshot=Decimal("0.00"),
            tax_total_snapshot=Decimal("0.00"),
            shipping_total_snapshot=Decimal("0.00"),
            grand_total_snapshot=Decimal("100.00"),
            paid_total_snapshot=Decimal("0.00"),
            outstanding_snapshot=Decimal("100.00"),
            payment_status_snapshot=Order.PaymentStatus.UNPAID,
            payment_method_snapshot=Order.PaymentMethod.UNSET,
            delivery_method_snapshot=Order.DeliveryMethod.SHIPPING,
        )
        response = self.client.get(
            reverse("core:management_invoice", args=[invoice.public_id])
        )
        self.assertNotContains(response, 'class="invoice-stamp"')

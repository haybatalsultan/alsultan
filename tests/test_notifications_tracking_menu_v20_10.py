from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import StoreSetting
from orders.models import Order, OrderNotification
from orders.services.notification_service import (
    notify_order_created,
    notify_order_status,
    notify_payment_received,
)

User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PUBLIC_BASE_URL="https://www.haybatalsultan.com",
)
class NotificationAndTrackingMenuV2010Tests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            "notify-customer", password="StrongPass!12345", email="buyer@example.com"
        )
        if hasattr(self.customer, "role"):
            self.customer.role = "CUSTOMER"
            self.customer.save(update_fields=["role"])
        self.owner = User.objects.create_user(
            "notify-owner", password="StrongPass!12345", email="owner@example.com"
        )
        if hasattr(self.owner, "role"):
            self.owner.role = "OWNER"
            self.owner.save(update_fields=["role"])
        StoreSetting.objects.update_or_create(
            singleton=True,
            defaults={
                "notification_email": "info@haybatalsultan.com",
                "notify_admin_new_order": True,
                "notify_admin_payment": True,
                "notify_customer_payment": True,
                "notify_customer_shipping": True,
            },
        )
        self.order = Order.objects.create(
            reference="HS-260822-NOTIFY",
            user=self.customer,
            customer_name="Buyer",
            customer_email="buyer@example.com",
            customer_phone="+971501234567",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("500.00"),
            grand_total=Decimal("500.00"),
            status=Order.Status.CONFIRMED,
            payment_status=Order.PaymentStatus.PAID,
            payment_method=Order.PaymentMethod.STRIPE,
        )

    def test_admin_new_order_notification_is_idempotent(self):
        notify_order_created(self.order.pk)
        notify_order_created(self.order.pk)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            OrderNotification.objects.filter(
                order=self.order, event_key="admin:new_order", sent=True
            ).count(),
            1,
        )
        self.assertIn("HS-260822-NOTIFY", mail.outbox[0].subject)
        self.assertNotIn("sk_", mail.outbox[0].body)
        self.assertNotIn("whsec_", mail.outbox[0].body)

    def test_payment_notification_sends_admin_and_customer_once(self):
        notify_payment_received(self.order.pk)
        notify_payment_received(self.order.pk)
        self.assertEqual(len(mail.outbox), 2)
        recipients = {message.to[0] for message in mail.outbox}
        self.assertEqual(recipients, {"info@haybatalsultan.com", "buyer@example.com"})

    def test_shipping_notification_does_not_expose_internal_payment_ids(self):
        self.order.status = Order.Status.SHIPPED
        self.order.shipping_carrier = "Aramex"
        self.order.tracking_number = "AWB-123"
        self.order.tracking_url = "https://example.com/AWB-123"
        self.order.save(
            update_fields=[
                "status",
                "shipping_carrier",
                "tracking_number",
                "tracking_url",
            ]
        )
        notify_order_status(self.order.pk, Order.Status.SHIPPED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("AWB-123", mail.outbox[0].body)
        self.assertNotIn("cs_test_", mail.outbox[0].body)

    def test_track_my_order_link_appears_only_with_active_customer_order(self):
        self.client.login(username="notify-customer", password="StrongPass!12345")
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "تتبع طلبي")
        self.order.status = Order.Status.DELIVERED
        self.order.save(update_fields=["status"])
        response = self.client.get(reverse("core:home"))
        self.assertNotContains(response, "تتبع طلبي")

    def test_notification_settings_are_owner_only(self):
        self.client.login(username="notify-customer", password="StrongPass!12345")
        response = self.client.get(reverse("core:management_notification_settings"))
        self.assertIn(response.status_code, {302, 403})

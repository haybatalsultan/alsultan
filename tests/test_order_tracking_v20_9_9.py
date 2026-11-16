from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from orders.models import Order, OrderItem, OrderTimelineEvent

User = get_user_model()


class SecureOrderTrackingV2099Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("track-v2099", password="StrongPass!12345")
        self.order = Order.objects.create(
            reference="HS-260822-TRACK99",
            user=self.user,
            customer_name="Tracking Customer",
            customer_phone="+971501234567",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("1250.00"),
            grand_total=Decimal("1250.00"),
            status=Order.Status.OUT_FOR_DELIVERY,
            payment_status=Order.PaymentStatus.PAID,
            payment_method=Order.PaymentMethod.STRIPE,
            shipping_carrier="Aramex",
            tracking_number="AWB-TRACK-99",
            tracking_url="https://example.com/track/AWB-TRACK-99",
        )
        OrderItem.objects.create(
            order=self.order,
            product_reference="HS00099",
            sku="HS00099",
            name_ar="مسباح اختبار",
            name_en="Tracking Misbah",
            unit_price=Decimal("1250.00"),
            quantity=1,
            line_total=Decimal("1250.00"),
        )
        OrderTimelineEvent.objects.create(
            order=self.order,
            kind=OrderTimelineEvent.Kind.STATUS_CHANGED,
            label_ar="خرج للتوصيل",
            label_en="Out for delivery",
            from_value=Order.Status.SHIPPED,
            to_value=Order.Status.OUT_FOR_DELIVERY,
        )

    def _track(self, phone=None):
        return self.client.post(
            reverse("orders:track"),
            {
                "reference": self.order.reference,
                "phone": phone or self.order.customer_phone,
            },
        )

    def test_matching_reference_and_phone_show_current_delivery_state(self):
        response = self._track()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HS00099")
        self.assertContains(response, "AWB-TRACK-99")
        self.assertContains(response, "Aramex")
        self.assertContains(response, "https://example.com/track/AWB-TRACK-99")
        self.assertContains(response, "خرج للتوصيل")

    def test_wrong_phone_does_not_leak_order_or_tracking_details(self):
        response = self._track("+971509999999")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "HS00099")
        self.assertNotContains(response, "AWB-TRACK-99")
        self.assertNotContains(response, "Aramex")

    def test_tracking_link_is_hardened_for_new_tab(self):
        response = self._track()
        self.assertContains(response, 'rel="noopener noreferrer nofollow"', html=False)

    def test_authenticated_customer_gets_my_orders_shortcut(self):
        self.client.login(username="track-v2099", password="StrongPass!12345")
        response = self.client.get(reverse("orders:track"))
        self.assertContains(response, reverse("orders:my_orders"))

    def test_tracking_form_keeps_two_factor_lookup_inputs(self):
        response = self.client.get(reverse("orders:track"))
        self.assertContains(response, 'name="reference"', html=False)
        self.assertContains(response, 'name="phone"', html=False)

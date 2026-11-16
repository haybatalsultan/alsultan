from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from orders.models import Order, OrderItem

User = get_user_model()


class CustomerOrdersScalingV2011Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "orders-v2011", password="StrongPass!12345"
        )
        self.other = User.objects.create_user(
            "orders-other-v2011", password="StrongPass!12345"
        )
        if hasattr(self.user, "role"):
            self.user.role = "CUSTOMER"
            self.user.save(update_fields=["role"])
            self.other.role = "CUSTOMER"
            self.other.save(update_fields=["role"])
        self.client.login(username="orders-v2011", password="StrongPass!12345")

    def _order(
        self,
        n,
        *,
        user=None,
        status=Order.Status.CONFIRMED,
        payment=Order.PaymentStatus.PAID,
    ):
        return Order.objects.create(
            reference=f"HS-V2011-{n:03d}",
            user=user or self.user,
            customer_name="Customer",
            customer_phone="+971501234567",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("100.00"),
            grand_total=Decimal("100.00"),
            status=status,
            payment_status=payment,
            payment_method=Order.PaymentMethod.STRIPE
            if payment == Order.PaymentStatus.PAID
            else Order.PaymentMethod.UNSET,
        )

    def test_my_orders_uses_ten_item_server_side_pagination(self):
        for n in range(13):
            self._order(n)
        response = self.client.get(reverse("orders:my_orders"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["orders"]), 10)
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)
        self.assertContains(response, "page=2")

    def test_search_is_scoped_to_authenticated_customer(self):
        own = self._order(20)
        other = self._order(21, user=self.other)
        response = self.client.get(
            reverse("orders:my_orders"), {"scope": "all", "q": "V2011"}
        )
        self.assertContains(response, own.reference)
        self.assertNotContains(response, other.reference)

    def test_paid_confirmed_are_rendered_as_distinct_arabic_status_badges(self):
        self._order(30)
        response = self.client.get(reverse("orders:my_orders"))
        self.assertContains(response, "تم الدفع")
        self.assertContains(response, "تم تأكيد الطلب")
        self.assertContains(response, "customer-status-badge", html=False)

    def test_completed_scope_excludes_active_orders(self):
        active = self._order(40)
        delivered = self._order(41, status=Order.Status.DELIVERED)
        response = self.client.get(reverse("orders:my_orders"), {"scope": "completed"})
        self.assertContains(response, delivered.reference)
        self.assertNotContains(response, active.reference)

    def test_detail_collapses_items_after_first_eight_and_shows_progress(self):
        order = self._order(50, status=Order.Status.OUT_FOR_DELIVERY)
        for n in range(10):
            OrderItem.objects.create(
                order=order,
                product_reference=f"HS{n:05d}",
                sku=f"HS{n:05d}",
                name_ar=f"قطعة {n}",
                name_en=f"Item {n}",
                unit_price=Decimal("10.00"),
                quantity=1,
                line_total=Decimal("10.00"),
            )
        response = self.client.get(reverse("orders:detail", args=[order.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "عرض بقية القطع (2)")
        self.assertContains(response, "خرج للتوصيل")
        self.assertContains(response, "customer-order-progress-card", html=False)

    def test_other_customer_cannot_open_detail_by_public_id(self):
        foreign = self._order(60, user=self.other)
        response = self.client.get(reverse("orders:detail", args=[foreign.public_id]))
        self.assertEqual(response.status_code, 404)

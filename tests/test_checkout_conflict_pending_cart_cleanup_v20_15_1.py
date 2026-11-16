from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from catalog.models import Category, Product
from orders.models import Cart, CartItem, Order, Reservation
from orders.services.cart_service import purge_abandoned_cart_items


@override_settings(RESERVATION_MINUTES=10, CART_ITEM_RETENTION_DAYS=30)
class CheckoutConflictPendingCartCleanupV20151Tests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(
            username="ahmed151", password="StrongPass!12345", role=User.Role.CUSTOMER
        )
        self.b = User.objects.create_user(
            username="saeed151", password="StrongPass!12345", role=User.Role.CUSTOMER
        )
        self.cat = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="misbah-151", is_active=True
        )
        self.p = Product.objects.create(
            category=self.cat,
            name_ar="قطعة",
            name_en="Item",
            available_quantity=1,
            reserved_quantity=0,
            cost_price="50.00",
            selling_price="100.00",
            status=Product.Status.AVAILABLE,
        )
        self.cart_a = Cart.objects.create(user=self.a)
        CartItem.objects.create(cart=self.cart_a, product=self.p, quantity=1)

    def _reserve_for_saeed(self):
        order = Order.objects.create(
            user=self.b,
            customer_name="Saeed",
            customer_phone="+971501111111",
            country="AE",
            area="AD",
            subtotal="100.00",
            grand_total="100.00",
        )
        Reservation.objects.create(
            order=order,
            product=self.p,
            quantity=1,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        Product.objects.filter(pk=self.p.pk).update(reserved_quantity=1)
        return order

    def test_checkout_get_warns_before_customer_fills_form_when_reserved_elsewhere(
        self,
    ):
        self._reserve_for_saeed()
        self.client.login(username="ahmed151", password="StrongPass!12345")
        response = self.client.get(reverse("orders:checkout"), follow=True)
        self.assertRedirects(response, reverse("orders:cart"))
        self.assertContains(response, self.p.sku)
        self.assertContains(response, "محجوزة مؤقتًا")

    def test_pending_order_in_my_orders_has_resume_payment_countdown(self):
        order = self._reserve_for_saeed()
        self.client.login(username="saeed151", password="StrongPass!12345")
        response = self.client.get(reverse("orders:my_orders"))
        self.assertContains(response, order.reference)
        self.assertContains(response, "قيد الدفع")
        self.assertContains(response, "إكمال الدفع")
        self.assertContains(response, "data-pending-order-expiry")

    def test_expired_pending_order_is_reconciled_before_my_orders_render(self):
        order = self._reserve_for_saeed()
        Reservation.objects.filter(order=order).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.client.login(username="saeed151", password="StrongPass!12345")
        response = self.client.get(reverse("orders:my_orders"))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertNotContains(response, "data-pending-order-expiry")

    def test_cart_item_older_than_30_days_is_housekeeping_only_and_deleted(self):
        item = self.cart_a.items.get()
        CartItem.objects.filter(pk=item.pk).update(
            updated_at=timezone.now() - timedelta(days=31)
        )
        deleted = purge_abandoned_cart_items(cart=self.cart_a)
        self.assertGreaterEqual(deleted, 1)
        self.p.refresh_from_db()
        self.assertEqual(self.p.reserved_quantity, 0)
        self.assertFalse(self.cart_a.items.exists())

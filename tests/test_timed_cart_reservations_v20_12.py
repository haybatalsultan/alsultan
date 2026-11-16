from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from orders.models import Reservation, ReservationLimitOverride
from orders.services.cart_service import add
from orders.services.order_service import create_order_from_cart

User = get_user_model()


@override_settings(
    RESERVATION_MINUTES=15,
    CHECKOUT_RESERVATION_MAX_ITEMS=3,
    CHECKOUT_RESERVATION_OVERRIDE_MAX=10,
    STORE_SHIPPING_FEE=Decimal("0.00"),
    STORE_TAX_RATE=Decimal("0.00"),
)
class AntiHoardingReservationV2013Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "cart-v2013", password="StrongPass!12345", email="buyer@example.com"
        )
        if hasattr(self.user, "role"):
            self.user.role = "CUSTOMER"
            self.user.save(update_fields=["role"])
        self.category = Category.objects.create(name_ar="مسابيح", name_en="Misbah")
        self.client.login(username="cart-v2013", password="StrongPass!12345")
        self.client.get(reverse("orders:cart"))
        self.cart = self.user.cart

    def product(self, qty=1, name="قطعة"):
        return Product.objects.create(
            name_ar=name,
            name_en="Piece",
            category=self.category,
            cost_price=Decimal(100),
            selling_price=Decimal(250),
            available_quantity=qty,
            reserved_quantity=0,
            status=Product.Status.AVAILABLE,
        )

    def customer(self):
        return {
            "customer_name": "Customer",
            "customer_email": "buyer@example.com",
            "customer_phone": "+971501234567",
            "country": "AE",
            "area": "Abu Dhabi",
            "policy_acceptance": True,
        }

    def test_add_to_cart_does_not_reserve_inventory(self):
        p = self.product()
        item = add(self.cart, p, 1)
        p.refresh_from_db()
        self.assertEqual(p.reserved_quantity, 0)
        self.assertIsNone(item.reserved_until)

    def test_checkout_starts_real_reservation(self):
        p = self.product()
        add(self.cart, p, 1)
        o = create_order_from_cart(
            cart=self.cart,
            customer=self.customer(),
            user=self.user,
            idempotency_key="checkout-hold",
        )
        p.refresh_from_db()
        self.assertEqual(p.reserved_quantity, 1)
        self.assertEqual(
            Reservation.objects.filter(
                order=o, product=p, released_at__isnull=True
            ).count(),
            1,
        )

    def test_default_limit_blocks_more_than_three(self):
        for i in range(4):
            add(self.cart, self.product(name=f"p{i}"), 1)
        with self.assertRaisesRegex(ValueError, "CHECKOUT_LIMIT:3"):
            create_order_from_cart(
                cart=self.cart,
                customer=self.customer(),
                user=self.user,
                idempotency_key="too-many",
            )

    def test_active_override_allows_more_than_three(self):
        for i in range(5):
            add(self.cart, self.product(name=f"p{i}"), 1)
        ReservationLimitOverride.objects.create(
            user=self.user,
            max_items=5,
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )
        o = create_order_from_cart(
            cart=self.cart,
            customer=self.customer(),
            user=self.user,
            idempotency_key="override-ok",
        )
        self.assertEqual(o.items.count(), 5)

    def test_expired_override_is_ignored(self):
        for i in range(4):
            add(self.cart, self.product(name=f"p{i}"), 1)
        ReservationLimitOverride.objects.create(
            user=self.user,
            max_items=10,
            expires_at=timezone.now() - timezone.timedelta(seconds=1),
        )
        with self.assertRaisesRegex(ValueError, "CHECKOUT_LIMIT:3"):
            create_order_from_cart(
                cart=self.cart,
                customer=self.customer(),
                user=self.user,
                idempotency_key="expired-override",
            )

    def test_cart_item_remains_visible_in_catalog_until_checkout(self):
        p = self.product()
        add(self.cart, p, 1)
        listing = self.client.get(reverse("catalog:list"))
        self.assertContains(listing, p.sku)

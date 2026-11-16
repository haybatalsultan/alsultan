from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Category, Product
from orders.models import Cart
from orders.services.cart_service import add, sanitize_cart
from orders.services.inventory_service import consume_order_reservations
from orders.services.order_service import create_order_from_cart

User = get_user_model()


@override_settings(
    RESERVATION_MINUTES=15,
    CHECKOUT_RESERVATION_MAX_ITEMS=3,
    CHECKOUT_RESERVATION_OVERRIDE_MAX=10,
    STORE_SHIPPING_FEE=Decimal("0.00"),
    STORE_TAX_RATE=Decimal("0.00"),
)
class CommerceHardeningV2014Tests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name_ar="مسابيح", name_en="Misbah")
        self.ahmed = User.objects.create_user(
            "ahmed-v2014", password="StrongPass!12345", email="ahmed@example.com"
        )
        self.saeed = User.objects.create_user(
            "saeed-v2014", password="StrongPass!12345", email="saeed@example.com"
        )
        for u in (self.ahmed, self.saeed):
            if hasattr(u, "role"):
                u.role = "CUSTOMER"
                u.save(update_fields=["role"])
        self.ahmed_cart = Cart.objects.create(user=self.ahmed)
        self.saeed_cart = Cart.objects.create(user=self.saeed)

    def product(self, name="مسباح", qty=1):
        return Product.objects.create(
            name_ar=name,
            name_en="Misbah",
            category=self.category,
            cost_price=Decimal(100),
            selling_price=Decimal(250),
            available_quantity=qty,
            reserved_quantity=0,
            status=Product.Status.AVAILABLE,
        )

    def customer(self, user, phone="+971501234567"):
        return {
            "customer_name": user.username,
            "customer_email": user.email,
            "customer_phone": phone,
            "country": "AE",
            "area": "Abu Dhabi",
            "policy_acceptance": True,
        }

    def test_ahmed_saeed_same_piece_sale_invalidates_ahmed_cart(self):
        p = self.product(name="HS scenario")
        add(self.ahmed_cart, p, 1)
        add(self.saeed_cart, p, 1)
        order = create_order_from_cart(
            cart=self.saeed_cart,
            customer=self.customer(self.saeed),
            user=self.saeed,
            idempotency_key="saeed-buys-first",
        )
        with self.captureOnCommitCallbacks(execute=True):
            consume_order_reservations(order, self.saeed)
        p.refresh_from_db()
        self.assertEqual(p.status, Product.Status.SOLD)
        self.assertFalse(self.ahmed_cart.items.filter(product=p).exists())

    def test_sanitize_cart_removes_sold_but_preserves_other_items(self):
        sold = self.product(name="sold")
        good = self.product(name="good")
        add(self.ahmed_cart, sold, 1)
        add(self.ahmed_cart, good, 1)
        sold.available_quantity = 0
        sold.status = Product.Status.SOLD
        sold.save(update_fields=["available_quantity", "status", "updated_at"])
        removed = sanitize_cart(self.ahmed_cart)
        self.assertEqual([r["sku"] for r in removed], [sold.sku])
        self.assertFalse(self.ahmed_cart.items.filter(product=sold).exists())
        self.assertTrue(self.ahmed_cart.items.filter(product=good).exists())

    def test_stale_cart_cannot_checkout_piece_reserved_by_other_customer(self):
        p = self.product()
        add(self.ahmed_cart, p, 1)
        add(self.saeed_cart, p, 1)
        create_order_from_cart(
            cart=self.saeed_cart,
            customer=self.customer(self.saeed),
            user=self.saeed,
            idempotency_key="saeed-reserves-first",
        )
        with self.assertRaisesRegex(ValueError, "unavailable"):
            create_order_from_cart(
                cart=self.ahmed_cart,
                customer=self.customer(self.ahmed, "+971501111111"),
                user=self.ahmed,
                idempotency_key="ahmed-stale-checkout",
            )

    def test_active_reservations_across_same_account_cannot_bypass_three_item_limit(
        self,
    ):
        for i in range(2):
            add(self.ahmed_cart, self.product(name=f"a{i}"), 1)
        create_order_from_cart(
            cart=self.ahmed_cart,
            customer=self.customer(self.ahmed),
            user=self.ahmed,
            idempotency_key="first-two",
        )
        for i in range(2):
            add(self.ahmed_cart, self.product(name=f"b{i}"), 1)
        with self.assertRaisesRegex(ValueError, "CHECKOUT_LIMIT:3"):
            create_order_from_cart(
                cart=self.ahmed_cart,
                customer=self.customer(self.ahmed),
                user=self.ahmed,
                idempotency_key="second-two",
            )

    def test_guest_same_phone_multiple_carts_cannot_bypass_limit(self):
        c1 = Cart.objects.create(user=None, session_key="guest-one")
        c2 = Cart.objects.create(user=None, session_key="guest-two")
        for i in range(2):
            add(c1, self.product(name=f"g1-{i}"), 1)
        for i in range(2):
            add(c2, self.product(name=f"g2-{i}"), 1)
        customer = self.customer(self.ahmed, "+971509999999")
        create_order_from_cart(
            cart=c1, customer=customer, user=None, idempotency_key="guest-first-two"
        )
        with self.assertRaisesRegex(ValueError, "CHECKOUT_LIMIT:3"):
            create_order_from_cart(
                cart=c2,
                customer=customer,
                user=None,
                idempotency_key="guest-second-two",
            )

    def test_cart_status_reports_changed_after_sale_invalidation(self):
        p = self.product()
        add(self.ahmed_cart, p, 1)
        self.client.force_login(self.ahmed)
        p.available_quantity = 0
        p.status = Product.Status.SOLD
        p.save(update_fields=["available_quantity", "status", "updated_at"])
        response = self.client.get(reverse("orders:cart_status"), {"count": 1})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["changed"])
        self.assertEqual(response.json()["cart_count"], 0)

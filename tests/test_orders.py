from decimal import Decimal

from django.test import TestCase

from accounts.models import User
from catalog.models import Category, Product
from orders.models import Cart, CartItem
from orders.services.order_service import create_order_from_cart


class OrderTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(
            "c", password="StrongPassword!123", role="CUSTOMER"
        )
        c = Category.objects.create(name_ar="كهرمان", name_en="Amber", slug="amber")
        self.p = Product.objects.create(
            sku="HS-1",
            name_ar="قطعة",
            name_en="Piece",
            category=c,
            cost_price=Decimal(10),
            selling_price=Decimal(100),
            available_quantity=1,
            status="AVAILABLE",
        )
        self.cart = Cart.objects.create(user=self.u)
        CartItem.objects.create(cart=self.cart, product=self.p, quantity=1)

    def data(self):
        return {
            "customer_name": "Test",
            "customer_email": "",
            "customer_phone": "+971501234567",
            "country": "AE",
            "emirate": "Abu Dhabi",
            "area": "Khalifa City",
            "street": "",
            "building": "",
            "apartment_or_villa": "",
            "additional_notes": "",
            "latitude": None,
            "longitude": None,
            "policy_acceptance": True,
        }

    def test_snapshot_and_reservation(self):
        o = create_order_from_cart(
            cart=self.cart, customer=self.data(), user=self.u, idempotency_key="abc"
        )
        item = o.items.get()
        self.assertEqual(item.unit_price, Decimal("100.00"))
        self.assertEqual(item.product_reference, self.p.product_reference)
        self.assertEqual(item.cost_unit_snapshot, Decimal("10.00"))
        self.assertEqual(item.cost_total_snapshot, Decimal("10.00"))
        self.p.refresh_from_db()
        self.assertEqual(self.p.reserved_quantity, 1)

    def test_idempotency(self):
        o1 = create_order_from_cart(
            cart=self.cart, customer=self.data(), user=self.u, idempotency_key="same"
        )
        o2 = create_order_from_cart(
            cart=self.cart, customer=self.data(), user=self.u, idempotency_key="same"
        )
        self.assertEqual(o1.pk, o2.pk)

    def test_order_rejected_without_policy_acceptance(self):
        data = self.data()
        data.pop("policy_acceptance", None)
        with self.assertRaises(ValueError):
            create_order_from_cart(
                cart=self.cart, customer=data, user=self.u, idempotency_key="no-policy"
            )


class AbandonedCartConsentTests(TestCase):
    def setUp(self):
        from django.urls import reverse

        self.reverse = reverse
        c = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="misbah-consent"
        )
        self.p = Product.objects.create(
            sku="HS-CONSENT",
            name_ar="مسبحة",
            name_en="Misbah",
            category=c,
            cost_price=Decimal(10),
            selling_price=Decimal(100),
            available_quantity=2,
            status="AVAILABLE",
        )

    def test_followup_requires_explicit_checkbox_and_valid_phone(self):
        # HTTP endpoint test also verifies CSRF-capable POST path and server-side validation.
        self.client.post(
            self.reverse("orders:cart_add", args=[self.p.public_id]), {"quantity": 1}
        )
        r = self.client.post(
            self.reverse("orders:cart_follow_up"), {"phone": "+971501234567"}
        )
        self.assertEqual(r.status_code, 400)
        cart = Cart.objects.get(session_key=self.client.session.session_key)
        self.assertIsNone(cart.whatsapp_opt_in_at)

    def test_guest_can_consent_then_revoke_and_phone_is_removed(self):
        self.client.post(
            self.reverse("orders:cart_add", args=[self.p.public_id]), {"quantity": 1}
        )
        r = self.client.post(
            self.reverse("orders:cart_follow_up"),
            {"phone": "+971501234567", "whatsapp_opt_in": "on"},
        )
        self.assertEqual(r.status_code, 302)
        cart = Cart.objects.get(session_key=self.client.session.session_key)
        self.assertIsNotNone(cart.whatsapp_opt_in_at)
        self.assertEqual(cart.contact_phone, "+971501234567")
        r = self.client.post(self.reverse("orders:cart_follow_up_cancel"))
        self.assertEqual(r.status_code, 302)
        cart.refresh_from_db()
        self.assertIsNone(cart.whatsapp_opt_in_at)
        self.assertEqual(cart.contact_phone, "")

    def test_followup_endpoints_reject_get(self):
        self.assertEqual(
            self.client.get(self.reverse("orders:cart_follow_up")).status_code, 405
        )
        self.assertEqual(
            self.client.get(self.reverse("orders:cart_follow_up_cancel")).status_code,
            405,
        )

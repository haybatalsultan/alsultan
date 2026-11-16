from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Category, Product
from orders.models import ReservationLimitRequest
from orders.services.cart_service import add

User = get_user_model()


@override_settings(
    CHECKOUT_RESERVATION_MAX_ITEMS=3, CHECKOUT_RESERVATION_OVERRIDE_MAX=10
)
class ReservationRequestCartV20132Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "limitbuyer", password="StrongPass!12345", email="limitbuyer@example.com"
        )
        if hasattr(self.user, "role"):
            self.user.role = "CUSTOMER"
            self.user.save(update_fields=["role"])
        self.cat = Category.objects.create(name_ar="مسابيح", name_en="Misbah")
        self.client.login(username="limitbuyer", password="StrongPass!12345")
        self.client.get(reverse("orders:cart"))
        self.cart = self.user.cart
        for i in range(5):
            p = Product.objects.create(
                name_ar=f"قطعة {i}",
                name_en=f"Piece {i}",
                category=self.cat,
                cost_price=Decimal(100),
                selling_price=Decimal(250),
                available_quantity=1,
                reserved_quantity=0,
                status=Product.Status.AVAILABLE,
            )
            add(self.cart, p, 1)

    def test_over_limit_cart_renders_request_and_whatsapp_actions(self):
        r = self.client.get(reverse("orders:cart"))
        self.assertContains(r, "طلب رفع الحد مؤقتًا")
        self.assertContains(r, "تواصل مع الإدارة عبر واتساب")
        self.assertContains(r, "5 قطع")

    def test_customer_request_is_server_derived_and_idempotent(self):
        url = reverse("orders:reservation_limit_request")
        self.client.post(url, {"requested_items": 99})
        req = ReservationLimitRequest.objects.get(user=self.user, status="PENDING")
        self.assertEqual(req.requested_items, 5)
        self.client.post(url, {"requested_items": 8})
        self.assertEqual(
            ReservationLimitRequest.objects.filter(
                user=self.user, status="PENDING"
            ).count(),
            1,
        )

    def test_request_endpoint_requires_authentication(self):
        self.client.logout()
        r = self.client.post(reverse("orders:reservation_limit_request"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/account/login/", r["Location"])

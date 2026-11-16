from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import Category, Product
from tests.helpers import login_management


class QuickSaleSecureSearchV20811Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="qs-search-owner",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        self.supervisor = User.objects.create_user(
            username="qs-search-supervisor",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        self.customer = User.objects.create_user(
            username="qs-search-customer",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )
        self.category = Category.objects.create(
            name_ar="مسابيح",
            name_en="Misbah",
            slug="qs-search-misbah",
        )
        self.available = Product.objects.create(
            name_ar="مسباح كهرمان بحث",
            name_en="Search Amber Misbah",
            category=self.category,
            cost_price=Decimal("600.00"),
            selling_price=Decimal("1500.00"),
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )
        self.reserved = Product.objects.create(
            name_ar="مسباح محجوز",
            name_en="Reserved Misbah",
            category=self.category,
            cost_price=Decimal("500.00"),
            selling_price=Decimal("1200.00"),
            available_quantity=1,
            reserved_quantity=1,
            status=Product.Status.AVAILABLE,
        )
        self.sold = Product.objects.create(
            name_ar="مسباح مباع",
            name_en="Sold Misbah",
            category=self.category,
            cost_price=Decimal("400.00"),
            selling_price=Decimal("1000.00"),
            available_quantity=0,
            status=Product.Status.SOLD,
        )
        login_management(self.client, self.owner, "VeryStrongPass!123")

    def search(self, q=""):
        return self.client.get(
            reverse("core:management_quick_sale_product_search"),
            {"q": q},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_owner_can_search_by_exact_sku(self):
        response = self.search(self.available.sku.lower())
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["sku"], self.available.sku)

    def test_owner_can_search_by_arabic_name(self):
        response = self.search("كهرمان")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["id"], self.available.pk)

    def test_reserved_and_sold_products_are_never_returned(self):
        response = self.search("")
        ids = {row["id"] for row in response.json()["results"]}
        self.assertIn(self.available.pk, ids)
        self.assertNotIn(self.reserved.pk, ids)
        self.assertNotIn(self.sold.pk, ids)

    def test_search_response_never_exposes_cost_or_profit(self):
        response = self.search(self.available.sku)
        row = response.json()["results"][0]
        forbidden = {
            "cost_price",
            "cost",
            "profit",
            "margin",
            "reserved_quantity",
            "available_quantity",
        }
        self.assertTrue(forbidden.isdisjoint(row.keys()))

    def test_search_is_bounded_to_ten_results(self):
        for idx in range(12):
            Product.objects.create(
                name_ar=f"قطعة بحث {idx}",
                name_en=f"Search Item {idx}",
                category=self.category,
                cost_price=Decimal("10.00"),
                selling_price=Decimal("100.00"),
                available_quantity=1,
                status=Product.Status.AVAILABLE,
            )
        response = self.search("")
        self.assertLessEqual(len(response.json()["results"]), 10)

    def test_supervisor_is_forbidden(self):
        self.client.logout()
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        response = self.search(self.available.sku)
        self.assertEqual(response.status_code, 403)

    def test_customer_is_forbidden(self):
        self.client.logout()
        self.client.login(
            username="qs-search-customer",
            password="VeryStrongPass!123",
        )
        response = self.search(self.available.sku)
        self.assertEqual(response.status_code, 403)

    def test_post_is_not_allowed_on_search_endpoint(self):
        response = self.client.post(
            reverse("core:management_quick_sale_product_search"),
            {"q": self.available.sku},
        )
        self.assertEqual(response.status_code, 405)

    def test_query_is_length_bounded_by_form(self):
        response = self.search("A" * 5000)
        self.assertEqual(response.status_code, 400)

    def test_search_does_not_change_inventory(self):
        before = (self.available.available_quantity, self.available.reserved_quantity)
        self.search(self.available.sku)
        self.available.refresh_from_db()
        self.assertEqual(
            (self.available.available_quantity, self.available.reserved_quantity),
            before,
        )

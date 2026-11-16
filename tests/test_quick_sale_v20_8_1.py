from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import Category, InventoryTransaction, Product
from core.models import AuditLog
from orders.models import Order
from tests.helpers import login_management


class QuickSaleV2081Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="qs-owner", password="VeryStrongPass!123", role=User.Role.OWNER
        )
        self.supervisor = User.objects.create_user(
            username="qs-supervisor", password="VeryStrongPass!123", role=User.Role.SUPERVISOR
        )
        self.customer = User.objects.create_user(
            username="qs-customer", password="VeryStrongPass!123", role=User.Role.CUSTOMER
        )
        self.category = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="qs-misbah"
        )
        self.product = Product.objects.create(
            name_ar="مسباح اختبار", name_en="Quick Sale Misbah",
            category=self.category, cost_price=Decimal("600.00"),
            selling_price=Decimal("1500.00"), available_quantity=1,
            status=Product.Status.AVAILABLE,
        )
        login_management(self.client, self.owner, "VeryStrongPass!123")

    def payload(self, **overrides):
        data = {
            "product": str(self.product.pk),
            "customer_name": "Direct Buyer",
            "customer_phone": "+971501234567",
            "customer_email": "buyer@example.com",
            "special_discount": "100.00",
            "payment_method": Order.PaymentMethod.CASH,
            "idempotency_key": "2b17961e-0b77-44b2-89ab-a7dbf4cb0a31",
        }
        data.update(overrides)
        return data

    def test_owner_can_open_quick_sale(self):
        response = self.client.get(reverse("core:management_quick_sale"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "بيع مباشر")

    def test_supervisor_is_forbidden_even_with_management_mfa(self):
        self.client.logout()
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        response = self.client.get(reverse("core:management_quick_sale"))
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_access_quick_sale(self):
        self.client.logout()
        self.client.login(username="qs-customer", password="VeryStrongPass!123")
        response = self.client.get(reverse("core:management_quick_sale"))
        self.assertEqual(response.status_code, 403)

    def test_successful_sale_is_paid_delivered_snapshotted_and_audited(self):
        response = self.client.post(reverse("core:management_quick_sale"), self.payload())
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(sale_channel=Order.SaleChannel.DIRECT)
        item = order.items.get()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.status, Order.Status.DELIVERED)
        self.assertEqual(order.payment_method, Order.PaymentMethod.CASH)
        self.assertEqual(order.grand_total, Decimal("1400.00"))
        self.assertEqual(item.base_unit_price, Decimal("1500.00"))
        self.assertEqual(item.unit_price, Decimal("1400.00"))
        self.assertEqual(item.cost_unit_snapshot, Decimal("600.00"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_quantity, 0)
        self.assertEqual(self.product.status, Product.Status.SOLD)
        self.assertTrue(InventoryTransaction.objects.filter(
            product=self.product, movement_type=InventoryTransaction.Type.SALE,
            order_reference=order.reference, quantity=-1,
        ).exists())
        self.assertTrue(AuditLog.objects.filter(
            action="order_quick_sale_created", object_reference=order.reference
        ).exists())

    def test_client_cannot_override_price_or_paid_status(self):
        data = self.payload(
            selling_price="1.00", grand_total="1.00", payment_status="REFUNDED",
            status="CANCELLED", cost_price="0.01",
        )
        self.client.post(reverse("core:management_quick_sale"), data)
        order = Order.objects.get(sale_channel=Order.SaleChannel.DIRECT)
        item = order.items.get()
        self.assertEqual(order.grand_total, Decimal("1400.00"))
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.status, Order.Status.DELIVERED)
        self.assertEqual(item.cost_unit_snapshot, Decimal("600.00"))

    def test_discount_equal_to_price_is_rejected_without_inventory_change(self):
        response = self.client.post(
            reverse("core:management_quick_sale"),
            self.payload(special_discount="1500.00"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.filter(sale_channel=Order.SaleChannel.DIRECT).count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_quantity, 1)

    def test_reserved_last_unit_is_not_available_for_direct_sale(self):
        self.product.reserved_quantity = 1
        self.product.save(update_fields=["reserved_quantity", "updated_at"])
        response = self.client.post(reverse("core:management_quick_sale"), self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.filter(sale_channel=Order.SaleChannel.DIRECT).count(), 0)

    def test_direct_sale_does_not_consume_another_customers_reserved_unit(self):
        self.product.available_quantity = 2
        self.product.reserved_quantity = 1
        self.product.status = Product.Status.AVAILABLE
        self.product.save(update_fields=["available_quantity", "reserved_quantity", "status", "updated_at"])
        response = self.client.post(reverse("core:management_quick_sale"), self.payload())
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_quantity, 1)
        self.assertEqual(self.product.reserved_quantity, 1)
        self.assertEqual(self.product.status, Product.Status.RESERVED)

    def test_duplicate_idempotency_key_does_not_create_second_sale(self):
        first = self.client.post(reverse("core:management_quick_sale"), self.payload())
        self.assertEqual(first.status_code, 302)
        # Re-post exactly the same request token.
        second = self.client.post(reverse("core:management_quick_sale"), self.payload())
        self.assertEqual(second.status_code, 200)  # product is no longer in bound form queryset
        self.assertEqual(Order.objects.filter(sale_channel=Order.SaleChannel.DIRECT).count(), 1)
        self.assertEqual(InventoryTransaction.objects.filter(
            product=self.product, movement_type=InventoryTransaction.Type.SALE
        ).count(), 1)

    def test_unavailable_product_cannot_be_sold_by_posting_its_pk(self):
        self.product.status = Product.Status.SOLD
        self.product.save(update_fields=["status", "updated_at"])
        response = self.client.post(reverse("core:management_quick_sale"), self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.filter(sale_channel=Order.SaleChannel.DIRECT).count(), 0)

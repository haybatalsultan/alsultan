from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import MFADevice, SupervisorPermission, User
from catalog.models import Category, Product
from orders.models import Order, OrderItem, OrderTimelineEvent
from tests.helpers import login_management


class OrderProofSecurityV196Tests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="misbah"
        )
        self.product = Product.objects.create(
            name_ar="مسباح اختبار",
            name_en="Test Misbah",
            category=self.category,
            cost_price=Decimal("100.00"),
            selling_price=Decimal("250.00"),
            available_quantity=3,
            status=Product.Status.AVAILABLE,
            verification_status=Product.VerificationStatus.INSPECTED,
        )
        self.owner = User.objects.create_user(
            "owner-v196", password="VeryStrongPass!123", role=User.Role.OWNER
        )
        MFADevice.objects.create(
            user=self.owner, secret="JBSWY3DPEHPK3PXP", enabled=True
        )

    def _order(self, user=None):
        order = Order.objects.create(
            reference="HS-260816-ABC123",
            user=user,
            customer_name="Customer",
            customer_phone="+971505939001",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("250.00"),
            grand_total=Decimal("250.00"),
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_reference=self.product.product_reference,
            sku=self.product.sku,
            name_ar=self.product.name_ar,
            name_en=self.product.name_en,
            base_unit_price=Decimal("250.00"),
            unit_price=Decimal("250.00"),
            quantity=1,
            line_total=Decimal("250.00"),
            verification_status_snapshot=Product.VerificationStatus.INSPECTED,
        )
        return order

    def test_my_orders_only_lists_authenticated_customers_own_orders(self):
        buyer = User.objects.create_user("buyer-list-v196", password="StrongPass!12345")
        other = User.objects.create_user("other-list-v196", password="StrongPass!12345")
        mine = self._order(buyer)
        other_order = Order.objects.create(
            reference="HS-260816-XYZ789",
            user=other,
            customer_name="Other",
            customer_phone="+971505939002",
            country="AE",
            area="Dubai",
            subtotal=Decimal("10.00"),
            grand_total=Decimal("10.00"),
        )
        self.client.login(username="buyer-list-v196", password="StrongPass!12345")
        response = self.client.get(reverse("orders:my_orders"))
        self.assertContains(response, mine.reference)
        self.assertNotContains(response, other_order.reference)

    def test_customer_cannot_open_another_customers_order_by_uuid(self):
        owner_of_order = User.objects.create_user(
            "buyer-v196", password="StrongPass!12345"
        )
        stranger = User.objects.create_user(
            "stranger-v196", password="StrongPass!12345"
        )
        order = self._order(owner_of_order)
        self.client.login(username="stranger-v196", password="StrongPass!12345")
        response = self.client.get(reverse("orders:detail", args=[order.public_id]))
        self.assertEqual(response.status_code, 404)

    def test_tracking_requires_matching_reference_and_phone(self):
        order = self._order()
        response = self.client.post(
            reverse("orders:track"),
            {
                "reference": order.reference,
                "phone": "+971501111111",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.product.product_reference)

        response = self.client.post(
            reverse("orders:track"),
            {
                "reference": order.reference,
                "phone": order.customer_phone,
            },
        )
        self.assertContains(response, self.product.product_reference)

    def test_order_item_snapshot_survives_product_changes(self):
        order = self._order()
        item = order.items.get()
        self.product.name_en = "Changed later"
        self.product.verification_status = Product.VerificationStatus.CERTIFIED
        self.product.save()
        item.refresh_from_db()
        self.assertEqual(item.name_en, "Test Misbah")
        self.assertEqual(
            item.verification_status_snapshot, Product.VerificationStatus.INSPECTED
        )

    def test_timeline_event_is_immutable(self):
        order = self._order()
        event = OrderTimelineEvent.objects.create(
            order=order,
            kind=OrderTimelineEvent.Kind.ORDER_CREATED,
            label_ar="تم إنشاء الطلب",
            label_en="Order created",
        )
        event.label_en = "Forged"
        with self.assertRaises(RuntimeError):
            event.save()
        with self.assertRaises(RuntimeError):
            event.delete()

    def test_supervisor_without_timeline_permission_does_not_receive_timeline(self):
        order = self._order()
        OrderTimelineEvent.objects.create(
            order=order,
            kind=OrderTimelineEvent.Kind.ORDER_CREATED,
            label_ar="تم إنشاء الطلب",
            label_en="Order created",
        )
        supervisor = User.objects.create_user(
            "supervisor-v196", password="VeryStrongPass!123", role=User.Role.SUPERVISOR
        )
        SupervisorPermission.objects.create(
            user=supervisor, view_orders=True, view_order_timeline=False
        )
        login_management(self.client, supervisor, "VeryStrongPass!123")
        response = self.client.get(
            reverse("core:management_order", args=[order.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "order-timeline")

    def test_abandoned_carts_requires_separate_permission(self):
        supervisor = User.objects.create_user(
            "cart-supervisor-v196",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        SupervisorPermission.objects.create(
            user=supervisor, view_orders=True, view_abandoned_carts=False
        )
        login_management(self.client, supervisor, "VeryStrongPass!123")
        response = self.client.get(reverse("core:management_abandoned_carts"))
        self.assertEqual(response.status_code, 403)

    def test_view_orders_alone_cannot_mark_order_delivered(self):
        order = self._order()
        Order.objects.filter(pk=order.pk).update(status=Order.Status.SHIPPED)
        supervisor = User.objects.create_user(
            "readonly-supervisor-v196",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        SupervisorPermission.objects.create(
            user=supervisor, view_orders=True, ship_orders=False
        )
        login_management(self.client, supervisor, "VeryStrongPass!123")
        response = self.client.post(
            reverse("core:management_order", args=[order.public_id]),
            {"action": "status", "order-status": Order.Status.DELIVERED},
        )
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)

    def test_invalid_status_jump_is_denied_even_to_owner(self):
        order = self._order()
        self.client.login(username="owner-v196", password="VeryStrongPass!123")
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session.save()
        response = self.client.post(
            reverse("core:management_order", args=[order.public_id]),
            {"action": "status", "order-status": Order.Status.DELIVERED},
        )
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

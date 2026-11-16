from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import MFADevice, SupervisorPermission, User
from orders.models import Order


class RoleAwareOrderPagesV20161Tests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer161",
            password="StrongPass!12345",
            role=User.Role.CUSTOMER,
        )

        self.other = User.objects.create_user(
            username="other161",
            password="StrongPass!12345",
            role=User.Role.CUSTOMER,
        )

        self.owner = User.objects.create_user(
            username="owner161",
            password="StrongPass!12345",
            role=User.Role.OWNER,
        )

        MFADevice.objects.create(
            user=self.owner,
            secret="A" * 32,
            enabled=True,
            confirmed_at=timezone.now(),
        )

        self.order = Order.objects.create(
            user=self.customer,
            customer_name="Customer",
            customer_phone="+971501234567",
            currency="AED",
            subtotal="100.00",
            grand_total="100.00",
        )

    def test_owner_customer_order_url_routes_to_management_surface(self):
        self.client.login(
            username="owner161",
            password="StrongPass!12345",
        )

        response = self.client.get(
            reverse(
                "orders:detail",
                args=[self.order.public_id],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "core:management_order",
                args=[self.order.public_id],
            ),
            fetch_redirect_response=False,
        )

    def test_owner_my_orders_routes_to_management_orders(self):
        self.client.login(
            username="owner161",
            password="StrongPass!12345",
        )

        response = self.client.get(reverse("orders:my_orders"))

        self.assertRedirects(
            response,
            reverse("core:management_orders"),
            fetch_redirect_response=False,
        )

    def test_other_customer_gets_branded_non_enumerating_404(self):
        self.client.login(
            username="other161",
            password="StrongPass!12345",
        )

        response = self.client.get(
            reverse(
                "orders:detail",
                args=[self.order.public_id],
            )
        )

        self.assertEqual(response.status_code, 404)

        self.assertTemplateUsed(
            response,
            "orders/order_not_available.html",
        )

        self.assertNotContains(
            response,
            self.order.customer_phone,
            status_code=404,
        )

        if self.order.reference:
            self.assertNotContains(
                response,
                self.order.reference,
                status_code=404,
            )

    def test_supervisor_without_view_orders_gets_branded_403(self):
        supervisor = User.objects.create_user(
            username="sup161",
            password="StrongPass!12345",
            role=User.Role.SUPERVISOR,
        )

        SupervisorPermission.objects.create(
            user=supervisor,
            view_orders=False,
        )

        MFADevice.objects.create(
            user=supervisor,
            secret="B" * 32,
            enabled=True,
            confirmed_at=timezone.now(),
        )

        self.client.login(
            username="sup161",
            password="StrongPass!12345",
        )

        response = self.client.get(
            reverse(
                "orders:detail",
                args=[self.order.public_id],
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTemplateUsed(
            response,
            "orders/order_access_denied.html",
        )

        self.assertNotContains(
            response,
            self.order.customer_phone,
            status_code=403,
        )

    def test_authorized_supervisor_routes_to_management_surface(self):
        supervisor = User.objects.create_user(
            username="supview161",
            password="StrongPass!12345",
            role=User.Role.SUPERVISOR,
        )

        SupervisorPermission.objects.create(
            user=supervisor,
            view_orders=True,
        )

        MFADevice.objects.create(
            user=supervisor,
            secret="C" * 32,
            enabled=True,
            confirmed_at=timezone.now(),
        )

        self.client.login(
            username="supview161",
            password="StrongPass!12345",
        )

        response = self.client.get(
            reverse(
                "orders:detail",
                args=[self.order.public_id],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "core:management_order",
                args=[self.order.public_id],
            ),
            fetch_redirect_response=False,
        )

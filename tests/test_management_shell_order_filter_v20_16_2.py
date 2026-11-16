from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import MFADevice, SupervisorPermission, User
from orders.models import Order


class ManagementShellOrderFilterV20162Tests(TestCase):
    def setUp(self):
        self.password = "StrongPass!12345"
        self.owner = User.objects.create_user(
            username="owner162",
            password=self.password,
            role=User.Role.OWNER,
        )
        MFADevice.objects.create(
            user=self.owner,
            secret="A" * 32,
            enabled=True,
            confirmed_at=timezone.now(),
        )
        self.pending = Order.objects.create(
            user=self.owner,
            reference="TEST-MGMT-001",
            customer_name="One",
            customer_phone="+971501111111",
            currency="AED",
            subtotal="10.00",
            grand_total="10.00",
            status=Order.Status.PENDING,
        )
        self.delivered = Order.objects.create(
            user=self.owner,
            reference="TEST-MGMT-002",
            customer_name="Two",
            customer_phone="+971502222222",
            currency="AED",
            subtotal="20.00",
            grand_total="20.00",
            status=Order.Status.DELIVERED,
        )

    def _login_with_mfa(self, user, username):
        logged_in = self.client.login(username=username, password=self.password)
        self.assertTrue(logged_in)
        session = self.client.session
        session["mfa_verified_user_id"] = str(user.pk)
        session["mfa_verified_at"] = timezone.now().timestamp()
        session.save()

    def test_owner_can_filter_orders_by_status(self):
        self._login_with_mfa(self.owner, "owner162")
        response = self.client.get(
            reverse("core:management_orders"),
            {"status": Order.Status.PENDING},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.pending.reference)
        self.assertNotContains(response, self.delivered.reference)

    def test_owner_can_filter_delivered_orders(self):
        self._login_with_mfa(self.owner, "owner162")
        response = self.client.get(
            reverse("core:management_orders"),
            {"status": Order.Status.DELIVERED},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.delivered.reference)
        self.assertNotContains(response, self.pending.reference)

    def test_invalid_status_filter_is_safely_ignored(self):
        self._login_with_mfa(self.owner, "owner162")
        response = self.client.get(
            reverse("core:management_orders"),
            {"status": "NOT-A-REAL-STATUS"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.pending.reference)
        self.assertContains(response, self.delivered.reference)

    def test_supervisor_without_view_orders_cannot_access_management_orders(self):
        supervisor = User.objects.create_user(
            username="sup162",
            password=self.password,
            role=User.Role.SUPERVISOR,
        )
        SupervisorPermission.objects.create(user=supervisor, view_orders=False)
        MFADevice.objects.create(
            user=supervisor,
            secret="B" * 32,
            enabled=True,
            confirmed_at=timezone.now(),
        )
        self._login_with_mfa(supervisor, "sup162")
        response = self.client.get(
            reverse("core:management_orders"),
            {"status": Order.Status.PENDING},
        )
        self.assertEqual(response.status_code, 403)

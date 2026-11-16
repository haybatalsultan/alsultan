from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import MFADevice, User


class ManagementUIV20163Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner163",
            password="StrongPass!12345",
            role=User.Role.OWNER,
        )
        MFADevice.objects.create(
            user=self.owner,
            secret="C" * 32,
            enabled=True,
            confirmed_at=timezone.now(),
        )
        self.client.login(username="owner163", password="StrongPass!12345")
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session["mfa_verified_at"] = timezone.now().timestamp()
        session.save()

    def test_management_page_loads_dedicated_stylesheet_and_shell(self):
        response = self.client.get(reverse("core:management_orders"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/css/management.css")
        self.assertContains(response, 'class="management-app-header"')
        self.assertNotContains(response, 'class="brand-header"')
        self.assertNotContains(response, "data-wishlist-header")
        self.assertNotContains(response, "data-cart-icon")

    def test_management_order_filter_keeps_server_side_controls(self):
        response = self.client.get(reverse("core:management_orders"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="status"')
        self.assertContains(response, 'name="q"')
        self.assertContains(response, 'class="management-order-filters"')

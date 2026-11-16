from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class ReservationOverrideManagementV2013Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "owner13", password="StrongPass!12345", email="owner13@example.com"
        )
        self.customer = User.objects.create_user(
            "customer13", password="StrongPass!12345", email="customer13@example.com"
        )
        if hasattr(self.owner, "role"):
            self.owner.role = "OWNER"
            self.owner.save(update_fields=["role"])
            self.customer.role = "CUSTOMER"
            self.customer.save(update_fields=["role"])

    def test_customer_cannot_open_management_override(self):
        self.client.login(username="customer13", password="StrongPass!12345")
        r = self.client.get(reverse("core:management_reservation_overrides"))
        self.assertIn(r.status_code, (302, 403))

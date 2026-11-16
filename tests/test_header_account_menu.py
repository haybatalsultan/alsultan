from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class HeaderAccountMenuTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="header-customer",
            email="header@example.com",
            first_name="Saeed",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )

    def test_authenticated_customer_name_and_logout_are_visible(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Saeed")
        self.assertContains(response, reverse("accounts:profile"))
        self.assertContains(response, 'action="' + reverse("accounts:logout") + '"')
        self.assertContains(response, 'method="post"')

    def test_logged_out_header_does_not_show_account_dropdown(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "header-account-dropdown")

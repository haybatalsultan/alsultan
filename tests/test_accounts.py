from django.test import TestCase
from django.urls import reverse

from accounts.forms import RegistrationForm
from accounts.models import User


class AccountFlowTests(TestCase):
    def test_customer_registration_forces_customer_role(self):
        form = RegistrationForm(
            data={
                "username": "customer1",
                "email": "Customer@Example.com",
                "first_name": "Test",
                "last_name": "Customer",
                "country": "AE",
                "phone_local": "0501234567",
                "password1": "VeryStrongPass!123",
                "password2": "VeryStrongPass!123",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertEqual(user.email, "customer@example.com")
        self.assertEqual(user.country, "AE")
        self.assertEqual(user.phone_e164, "+971501234567")

    def test_duplicate_email_case_insensitive_rejected(self):
        User.objects.create_user(
            username="existing", email="user@example.com", password="VeryStrongPass!123"
        )
        form = RegistrationForm(
            data={
                "username": "second",
                "email": "USER@example.com",
                "first_name": "Second",
                "last_name": "User",
                "country": "AE",
                "phone_local": "0501234568",
                "password1": "VeryStrongPass!123",
                "password2": "VeryStrongPass!123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_invalid_phone_rejected(self):
        form = RegistrationForm(
            data={
                "username": "badphone",
                "email": "bad@example.com",
                "country": "AE",
                "phone_local": "12",
                "password1": "VeryStrongPass!123",
                "password2": "VeryStrongPass!123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("phone_local", form.errors)

    def test_owner_login_requires_mfa_setup_before_management(self):
        User.objects.create_user(
            username="ownerlogin",
            email="owner@example.com",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "ownerlogin", "password": "VeryStrongPass!123"},
        )
        self.assertRedirects(
            response, reverse("accounts:mfa_setup"), fetch_redirect_response=False
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_customer_login_redirects_home(self):
        User.objects.create_user(
            username="customerlogin",
            email="c@example.com",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "customerlogin", "password": "VeryStrongPass!123"},
        )
        self.assertRedirects(
            response, reverse("core:home"), fetch_redirect_response=False
        )

import pyotp
from django.test import TestCase
from django.urls import reverse

from accounts.models import MFADevice, User


class LocalAuthenticationBackendRegressionTests(TestCase):
    def test_customer_registration_can_login_with_multiple_backends(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "backend-customer",
                "email": "backend-customer@example.com",
                "first_name": "Backend",
                "last_name": "Customer",
                "country": "AE",
                "phone_local": "0501234567",
                "password1": "VeryStrongPass!123",
                "password2": "VeryStrongPass!123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(
            self.client.session.get("_auth_user_backend"),
            "django.contrib.auth.backends.ModelBackend",
        )

    def test_owner_mfa_verification_uses_local_model_backend(self):
        owner = User.objects.create_user(
            username="backend-owner",
            email="backend-owner@example.com",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        device = MFADevice.objects.create(
            user=owner,
            secret=pyotp.random_base32(),
            enabled=True,
        )

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "backend-owner",
                "password": "VeryStrongPass!123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)

        response = self.client.post(
            reverse("accounts:mfa_verify"),
            {"code": pyotp.TOTP(device.secret).now()},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(
            self.client.session.get("_auth_user_backend"),
            "django.contrib.auth.backends.ModelBackend",
        )

    def test_owner_mfa_enrollment_uses_local_model_backend(self):
        owner = User.objects.create_user(
            username="backend-owner-new",
            email="backend-owner-new@example.com",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "backend-owner-new",
                "password": "VeryStrongPass!123",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.client.get(reverse("accounts:mfa_setup"))
        device = MFADevice.objects.get(user=owner)

        response = self.client.post(
            reverse("accounts:mfa_setup"),
            {"code": pyotp.TOTP(device.secret).now()},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(
            self.client.session.get("_auth_user_backend"),
            "django.contrib.auth.backends.ModelBackend",
        )

from types import SimpleNamespace

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from accounts.social_adapters import HaybatSocialAccountAdapter


class GoogleOAuthConfigurationTests(TestCase):
    def test_regular_allauth_signup_redirects_to_store_registration(self):
        response = self.client.get("/accounts/signup/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:register"))

    def test_regular_allauth_login_redirects_to_store_login(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:login"))

    @override_settings(GOOGLE_OAUTH_ENABLED=True)
    def test_store_login_shows_google_button_when_configured(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "google-login-btn")
        self.assertContains(response, 'method="post"')

    def test_security_settings_disable_email_auto_link_and_token_storage(self):
        from django.conf import settings

        self.assertFalse(settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION)
        self.assertFalse(settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT)
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
        self.assertFalse(settings.SOCIALACCOUNT_STORE_TOKENS)
        self.assertTrue(
            settings.SOCIALACCOUNT_PROVIDERS["google"]["OAUTH_PKCE_ENABLED"]
        )


class GoogleOAuthPrivilegeIsolationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_owner_cannot_use_social_login_as_management_authentication(self):
        owner = User.objects.create_user(
            username="oauth-owner",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        request = self.factory.get("/")
        request.user = owner
        sociallogin = SimpleNamespace(
            is_existing=False,
            account=SimpleNamespace(user=None),
        )
        adapter = HaybatSocialAccountAdapter(request)
        with self.assertRaises(PermissionDenied):
            adapter.pre_social_login(request, sociallogin)

    def test_supervisor_cannot_connect_social_login(self):
        supervisor = User.objects.create_user(
            username="oauth-supervisor",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        request = self.factory.get("/")
        request.user = supervisor
        sociallogin = SimpleNamespace(
            is_existing=False,
            account=SimpleNamespace(user=None),
        )
        adapter = HaybatSocialAccountAdapter(request)
        with self.assertRaises(PermissionDenied):
            adapter.pre_social_login(request, sociallogin)

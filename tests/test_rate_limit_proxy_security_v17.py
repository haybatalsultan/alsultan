from unittest.mock import patch

from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.models import SecurityEvent, User
from accounts.services.security_service import client_ip, record_event


class ForwardedHeaderTrustBoundaryTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    def test_client_ip_ignores_spoofed_forwarding_headers(self):
        request = self.factory.get(
            "/",
            REMOTE_ADDR="10.20.30.40",
            HTTP_X_FORWARDED_FOR="1.1.1.1, 2.2.2.2",
            HTTP_CF_CONNECTING_IP="8.8.8.8",
        )
        self.assertEqual(client_ip(request), "10.20.30.40")

    def test_audit_security_event_does_not_treat_forwarded_ip_as_authoritative(self):
        request = self.factory.get(
            "/",
            REMOTE_ADDR="10.20.30.40",
            HTTP_X_FORWARDED_FOR="1.1.1.1",
            HTTP_CF_CONNECTING_IP="8.8.8.8",
            HTTP_USER_AGENT="security-test",
        )
        record_event(request, "proxy_spoof_test")
        event = SecurityEvent.objects.latest("created_at")
        self.assertEqual(str(event.ip_address), "10.20.30.40")
        self.assertNotEqual(str(event.ip_address), "1.1.1.1")
        self.assertNotEqual(str(event.ip_address), "8.8.8.8")
        self.assertEqual(event.details.get("forwarded_ip_trusted"), False)
        self.assertNotIn("1.1.1.1", str(event.details))


class AuthenticationRateLimitSpoofingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="rate-limit-user",
            email="ratelimit@example.com",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )

    def tearDown(self):
        cache.clear()

    def test_rotating_x_forwarded_for_cannot_bypass_login_account_limit(self):
        url = reverse("accounts:login")

        # Ten bad attempts are allowed by the configured fixed window.
        for attempt in range(10):
            response = self.client.post(
                url,
                {
                    "username": self.user.username,
                    "password": "WrongPassword!999",
                },
                REMOTE_ADDR="10.0.0.5",
                HTTP_X_FORWARDED_FOR=f"198.51.100.{attempt + 1}",
                HTTP_CF_CONNECTING_IP=f"203.0.113.{attempt + 1}",
            )
            self.assertNotEqual(response.status_code, 429)

        # Changing both attacker-controlled forwarding headers still hits the
        # stable username bucket on the 11th attempt.
        response = self.client.post(
            url,
            {
                "username": self.user.username,
                "password": "WrongPassword!999",
            },
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="192.0.2.200",
            HTTP_CF_CONNECTING_IP="192.0.2.201",
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "300")

    def test_rotating_forwarded_headers_cannot_bypass_password_reset_email_limit(self):
        url = reverse("accounts:password_reset")

        for attempt in range(5):
            response = self.client.post(
                url,
                {"email": "unknown@example.com"},
                REMOTE_ADDR="10.0.0.9",
                HTTP_X_FORWARDED_FOR=f"198.51.100.{attempt + 30}",
            )
            self.assertNotEqual(response.status_code, 429)

        response = self.client.post(
            url,
            {"email": "unknown@example.com"},
            REMOTE_ADDR="10.0.0.9",
            HTTP_X_FORWARDED_FOR="203.0.113.250",
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "900")

    @override_settings(RATE_LIMIT_FAIL_CLOSED=True)
    def test_production_policy_fails_closed_when_shared_cache_breaks(self):
        with patch(
            "core.middleware.cache.add", side_effect=RuntimeError("cache unavailable")
        ):
            response = self.client.post(
                reverse("accounts:login"),
                {
                    "username": self.user.username,
                    "password": "WrongPassword!999",
                },
                REMOTE_ADDR="10.0.0.10",
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["Cache-Control"], "no-store")


class ProductionRateLimitConfigurationTests(TestCase):
    def test_render_blueprint_defines_shared_key_value_cache(self):
        from pathlib import Path

        from django.conf import settings

        render_yaml = (Path(settings.BASE_DIR) / "render.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("type: keyvalue", render_yaml)
        self.assertIn("name: haybat-security-cache", render_yaml)
        self.assertIn("key: REDIS_URL", render_yaml)
        self.assertIn("property: connectionString", render_yaml)

    def test_forwarded_headers_are_not_used_directly_by_rate_limit_middleware(self):
        from pathlib import Path

        from django.conf import settings

        middleware = (Path(settings.BASE_DIR) / "core" / "middleware.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("HTTP_CF_CONNECTING_IP", middleware)
        self.assertNotIn("HTTP_X_FORWARDED_FOR", middleware)

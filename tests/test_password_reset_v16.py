from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import User


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="HaybatAlsultan <info@haybatalsultan.com>",
)
class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reset-customer",
            email="reset@example.com",
            password="OldStrongPass!123",
            role=User.Role.CUSTOMER,
        )

    def test_password_reset_post_uses_namespaced_done_url(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": self.user.email},
        )
        self.assertRedirects(
            response,
            reverse("accounts:password_reset_done"),
            fetch_redirect_response=False,
        )

    def test_password_reset_email_contains_namespaced_confirm_url(self):
        self.client.post(
            reverse("accounts:password_reset"),
            {"email": self.user.email},
        )
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertIn("/account/reset/", body)
        self.assertNotIn("password_reset_confirm", body)

    def test_unknown_email_gets_same_generic_redirect(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "unknown@example.com"},
        )
        self.assertRedirects(
            response,
            reverse("accounts:password_reset_done"),
            fetch_redirect_response=False,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_done_page_does_not_disclose_account_existence(self):
        response = self.client.get(reverse("accounts:password_reset_done"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "لا نؤكد")

    def test_valid_token_can_set_new_password_and_reaches_complete_page(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        initial_url = reverse(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": uid, "token": token},
        )

        first = self.client.get(initial_url)
        self.assertEqual(first.status_code, 302)
        set_password_url = first["Location"]

        response = self.client.post(
            set_password_url,
            {
                "new_password1": "NewStrongPass!456",
                "new_password2": "NewStrongPass!456",
            },
        )
        self.assertRedirects(
            response,
            reverse("accounts:password_reset_complete"),
            fetch_redirect_response=False,
        )

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass!456"))

    def test_invalid_token_does_not_show_password_form(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.get(
            reverse(
                "accounts:password_reset_confirm",
                kwargs={"uidb64": uid, "token": "invalid-token"},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "الرابط غير صالح")

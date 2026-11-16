from django.conf import settings
from django.test import SimpleTestCase


class GoogleOAuthCSPTests(SimpleTestCase):
    def test_google_accounts_allowed_only_for_form_action(self):
        form_action = settings.SECURE_CSP["form-action"]
        self.assertIn("https://accounts.google.com", form_action)
        self.assertIn("'self'", [str(item) for item in form_action])

    def test_google_accounts_not_added_to_script_or_connect_sources(self):
        self.assertNotIn(
            "https://accounts.google.com",
            settings.SECURE_CSP["script-src"],
        )
        self.assertNotIn(
            "https://accounts.google.com",
            settings.SECURE_CSP["connect-src"],
        )

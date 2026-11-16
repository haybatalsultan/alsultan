from django.conf import settings
from django.test import SimpleTestCase


class WhatsAppCspV20183Tests(SimpleTestCase):
    def test_whatsapp_hosts_are_allowed_for_form_redirect_chain(self):
        form_action = settings.SECURE_CSP.get("form-action", [])
        self.assertIn("https://wa.me", form_action)
        self.assertIn("https://api.whatsapp.com", form_action)

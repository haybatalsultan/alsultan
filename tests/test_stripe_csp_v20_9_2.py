from django.conf import settings
from django.test import SimpleTestCase


class StripeCheckoutCSPTests(SimpleTestCase):
    def test_checkout_host_is_allowed_for_form_redirect_chain(self):
        form_action = settings.SECURE_CSP["form-action"]
        self.assertIn("https://checkout.stripe.com", form_action)

    def test_stripe_csp_permission_is_narrow(self):
        form_action = settings.SECURE_CSP["form-action"]
        self.assertNotIn("https://*.stripe.com", form_action)
        self.assertNotIn("*", [str(item) for item in form_action])
        self.assertNotIn(
            "https://checkout.stripe.com", settings.SECURE_CSP["script-src"]
        )
        self.assertNotIn(
            "https://checkout.stripe.com", settings.SECURE_CSP["connect-src"]
        )

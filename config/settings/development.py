from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Use real SMTP locally when EMAIL_HOST is configured; otherwise keep the
# console backend for offline development/testing.
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST
    else "django.core.mail.backends.console.EmailBackend"
)

if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise RuntimeError("EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled.")

# Never allow live Stripe credentials in local development.
if STRIPE_ENABLED and (
    STRIPE_PUBLISHABLE_KEY.startswith("pk_live_")
    or STRIPE_SECRET_KEY.startswith("sk_live_")
):
    raise RuntimeError(
        "Live Stripe keys are blocked in development. Use Sandbox/Test keys."
    )

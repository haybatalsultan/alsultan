from .base import *

DEBUG = False

# Fast password hashing for automated tests only.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "haybat-tests",
    }
}

# Tests must not depend on a previously generated staticfiles manifest.
# Production keeps WhiteNoise CompressedManifestStaticFilesStorage.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Automated tests must never make real Stripe API calls unless a test explicitly overrides these settings.
STRIPE_ENABLED = False
STRIPE_PUBLISHABLE_KEY = ""
STRIPE_SECRET_KEY = ""
STRIPE_WEBHOOK_SECRET = ""

from decimal import Decimal
from pathlib import Path

import dj_database_url
from django.utils.csp import CSP

from config.env import env, env_bool, env_int, env_list

GOOGLE_MAPS_API_ORIGIN = 'https://maps.googleapis.com'
GOOGLE_MAPS_STATIC_ORIGIN = 'https://maps.gstatic.com'

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "django_countries",
    "accounts.apps.AccountsConfig",
    "catalog.apps.CatalogConfig",
    "orders.apps.OrdersConfig",
    "core.apps.CoreConfig",
    "ambassadors.apps.AmbassadorsConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "core.middleware.RequestIDMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "core.middleware.DefaultArabicLanguageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "core.middleware.ManagementSecurityAuditMiddleware",
    "core.middleware.ManagementMFAEnforcementMiddleware",
    "core.middleware.SensitiveEndpointRateLimitMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.template.context_processors.csp",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.store_context",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASE_URL = env("DATABASE_URL").strip()
DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=60,
        conn_health_checks=True,
    )
}
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
LANGUAGE_CODE = "ar"
LANGUAGES = [("ar", "العربية"), ("en", "English")]
TIME_ZONE = "Asia/Dubai"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 60 * 60 * 8
SESSION_SAVE_EVERY_REQUEST = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
DATA_UPLOAD_MAX_MEMORY_SIZE = 65 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "base-uri": [CSP.SELF],
    "object-src": [CSP.NONE],
    "frame-ancestors": [CSP.NONE],
    "form-action": [
        CSP.SELF,
        "https://accounts.google.com",
        "https://checkout.stripe.com",
        "https://wa.me",
        "https://api.whatsapp.com",
    ],
    "script-src": [
        CSP.SELF,
        CSP.NONCE,
        "https://cdn.jsdelivr.net",
        GOOGLE_MAPS_API_ORIGIN,
        GOOGLE_MAPS_STATIC_ORIGIN,
    ],
    "style-src": [
        CSP.SELF,
        CSP.NONCE,
        "https://cdn.jsdelivr.net",
        "https://fonts.googleapis.com",
    ],
    "img-src": [
        CSP.SELF,
        "data:",
        "https://res.cloudinary.com",
        GOOGLE_MAPS_STATIC_ORIGIN,
        GOOGLE_MAPS_API_ORIGIN,
    ],
    "font-src": [CSP.SELF, "https://fonts.gstatic.com"],
    "connect-src": [
        CSP.SELF,
        GOOGLE_MAPS_API_ORIGIN,
        GOOGLE_MAPS_STATIC_ORIGIN,
    ],
}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "haybat-default",
    }
}
REDIS_URL = env("REDIS_URL")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
RATE_LIMIT_FAIL_CLOSED = env_bool("RATE_LIMIT_FAIL_CLOSED", False)
RATE_LIMIT_USE_NETWORK_PEER = env_bool("RATE_LIMIT_USE_NETWORK_PEER", True)
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if env("EMAIL_HOST")
    else "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
CLOUDINARY_CLOUD_NAME = env("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = env("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = env("CLOUDINARY_API_SECRET")
PRODUCT_IMAGE_MAX_BYTES = env_int("PRODUCT_IMAGE_MAX_BYTES", 5 * 1024 * 1024)
PRODUCT_IMAGE_MAX_COUNT = env_int("PRODUCT_IMAGE_MAX_COUNT", 12)
PRODUCT_IMAGE_MAX_PIXELS = env_int("PRODUCT_IMAGE_MAX_PIXELS", 40000000)
STORE_CONTACT_PHONE = env("STORE_CONTACT_PHONE", "+971504084006")
STORE_CONTACT_EMAIL = env("STORE_CONTACT_EMAIL") or "info@haybatalsultan.com"
PUBLIC_BASE_URL = (env("PUBLIC_BASE_URL") or "").strip().rstrip("/")
STORE_SOCIAL_HANDLE = env("STORE_SOCIAL_HANDLE") or "HaybatAlsultan"
DEFAULT_FROM_EMAIL = (
    env("DEFAULT_FROM_EMAIL") or f"HaybatAlsultan <{STORE_CONTACT_EMAIL}>"
)
WHATSAPP_NUMBER = env("WHATSAPP_NUMBER") or STORE_CONTACT_PHONE
RESERVATION_MINUTES = env_int("RESERVATION_MINUTES", 10)
CHECKOUT_RESERVATION_MAX_ITEMS = env_int("CHECKOUT_RESERVATION_MAX_ITEMS", 3)
CHECKOUT_RESERVATION_OVERRIDE_MAX = env_int("CHECKOUT_RESERVATION_OVERRIDE_MAX", 10)
ABANDONED_CART_MINUTES = env_int("ABANDONED_CART_MINUTES", 45)
CART_ITEM_RETENTION_DAYS = env_int("CART_ITEM_RETENTION_DAYS", 30)
STORE_TAX_RATE = Decimal(env("STORE_TAX_RATE", "0.00"))
STORE_SHIPPING_FEE = Decimal(env("STORE_SHIPPING_FEE", "0.00"))
GOOGLE_MAPS_API_KEY = env("GOOGLE_MAPS_API_KEY")
GOOGLE_MAPS_GEOCODING_API_KEY = env("GOOGLE_MAPS_GEOCODING_API_KEY")
GOOGLE_OAUTH_CLIENT_ID = env("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = env("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_OAUTH_ENABLED = bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET)

# Stripe Checkout. Secrets are loaded only from environment variables and are
# never embedded in templates or committed source.
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET")
STRIPE_CURRENCY = (env("STRIPE_CURRENCY", "aed") or "aed").strip().lower()
STRIPE_CHECKOUT_MINUTES = max(30, min(env_int("STRIPE_CHECKOUT_MINUTES", 30), 1440))
STRIPE_ENABLED = env_bool(
    "STRIPE_ENABLED", bool(STRIPE_PUBLISHABLE_KEY and STRIPE_SECRET_KEY)
)
if STRIPE_ENABLED:
    if not (
        STRIPE_PUBLISHABLE_KEY.startswith(("pk_test_", "pk_live_"))
        and STRIPE_SECRET_KEY.startswith(("sk_test_", "sk_live_"))
    ):
        raise RuntimeError("Stripe API keys have invalid prefixes.")
    if STRIPE_PUBLISHABLE_KEY[3:7] != STRIPE_SECRET_KEY[3:7]:
        raise RuntimeError("Stripe publishable and secret keys must use the same mode.")

SOCIALACCOUNT_ADAPTER = "accounts.social_adapters.HaybatSocialAccountAdapter"
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = False
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_FORMS = {"signup": "accounts.social_forms.GoogleSocialSignupForm"}
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "secret": GOOGLE_OAUTH_CLIENT_SECRET,
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "OAUTH_PKCE_ENABLED": True,
    }
}
ACCOUNT_LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_SIGNUP_FIELDS = ["email*"]
ACCOUNT_SIGNUP_REDIRECT_URL = "/ambassador/"
ACCOUNT_LOGIN_METHODS = {"email"}
SENTRY_DSN = env("SENTRY_DSN")
AUDIT_LOG_SIGNING_KEY = env("AUDIT_LOG_SIGNING_KEY")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "{levelname} {asctime} {name} {message}", "style": "{"}
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"}
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "haybat.security": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

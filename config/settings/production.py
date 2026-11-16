from config.env import env_int

from .base import *

if SECRET_KEY in {"", "dev-only-change-me"}:
    raise RuntimeError("DJANGO_SECRET_KEY must be configured in production.")
if not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS must be configured in production.")
if not REDIS_URL:
    raise RuntimeError(
        "REDIS_URL must be configured in production so security rate limits "
        "are shared across all workers."
    )
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise RuntimeError("EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled.")
if not AUDIT_LOG_SIGNING_KEY:
    raise RuntimeError("AUDIT_LOG_SIGNING_KEY must be configured in production.")

DEBUG = False
RATE_LIMIT_FAIL_CLOSED = True
# Render's REMOTE_ADDR is an edge/load-balancer peer shared by many users.
# Never apply low per-client limits to it in production.
RATE_LIMIT_USE_NETWORK_PEER = False

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Render terminates TLS before forwarding the request to Gunicorn.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False

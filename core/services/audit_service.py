import hashlib
import hmac
import json
from decimal import Decimal
from uuid import UUID

from django.conf import settings

from accounts.services.security_service import client_ip
from core.models import AuditLog

SENSITIVE_KEYS = {
    "password",
    "password1",
    "password2",
    "new_password1",
    "new_password2",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "mfa_secret",
    "otp",
    "code",
    "authorization",
    "cookie",
    "sessionid",
    "csrfmiddlewaretoken",
    "client_secret",
    "api_key",
    "webhook_secret",
    "email_host_password",
}

CATEGORY_PREFIXES = {
    "product_": "PRODUCT",
    "pricing_": "PRICING",
    "inventory_": "INVENTORY",
    "order_": "ORDER",
    "payment_": "PAYMENT",
    "expense_": "FINANCE",
    "invoice_": "FINANCE",
    "promotion_": "PROMOTION",
    "category_": "MASTER_DATA",
    "material_": "MASTER_DATA",
    "supervisor_": "ACCESS_CONTROL",
    "address_": "ACCOUNT",
    "wishlist_": "CUSTOMER_ACTIVITY",
    "cart_": "CART",
    "checkout_": "ORDER",
}


def _safe_scalar(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except (TypeError, ValueError, OverflowError):
            # Some third-party values expose isoformat() but cannot serialize safely.
            # Fall through to the bounded scalar representation below.
            pass
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)[:500]


def sanitize(value, *, key=""):
    """
    Recursively remove secret-bearing fields before writing to the audit store.
    This is intentionally server-side; templates and callers are not trusted to
    remember every sensitive key.
    """
    lowered = str(key).strip().casefold()
    if lowered in SENSITIVE_KEYS or any(
        marker in lowered
        for marker in ("password", "secret", "token", "authorization", "cookie")
    ):
        return "[REDACTED]"

    if isinstance(value, dict):
        return {str(k)[:120]: sanitize(v, key=k) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize(item) for item in value][:100]
    return _safe_scalar(value)


def action_category(action):
    for prefix, category in CATEGORY_PREFIXES.items():
        if action.startswith(prefix):
            return category
    return "GENERAL"


def _source_for(request):
    path = getattr(request, "path", "") or ""
    return (
        AuditLog.Source.MANAGEMENT
        if path.startswith("/management/")
        else AuditLog.Source.STOREFRONT
    )


def _object_reference(obj):
    return (
        getattr(obj, "product_reference", None)
        or getattr(obj, "reference", None)
        or getattr(obj, "public_id", None)
        or getattr(obj, "pk", "")
    )


def _integrity_digest(payload):
    key = getattr(settings, "AUDIT_LOG_SIGNING_KEY", "") or settings.SECRET_KEY
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hmac.new(
        key.encode("utf-8"),
        canonical,
        hashlib.sha256,
    ).hexdigest()


def audit(
    request,
    action,
    obj,
    old=None,
    new=None,
    *,
    metadata=None,
    outcome=AuditLog.Outcome.SUCCESS,
    source=None,
):
    user = getattr(request, "user", None)
    actor = user if getattr(user, "is_authenticated", False) else None
    actor_username = getattr(actor, "username", "") if actor else ""
    actor_role = getattr(actor, "role", "") if actor else ""

    old_values = sanitize(old or {})
    new_values = sanitize(new or {})
    safe_metadata = sanitize(metadata or {})

    payload = {
        "actor_username": actor_username,
        "actor_role": actor_role,
        "action": action,
        "category": action_category(action),
        "outcome": outcome,
        "source": source or _source_for(request),
        "object_type": obj.__class__.__name__,
        "object_reference": str(_object_reference(obj)),
        "request_id": str(getattr(request, "request_id", ""))[:64],
        "http_method": str(getattr(request, "method", ""))[:10],
        "path": str(getattr(request, "path", ""))[:300],
        "ip_address": client_ip(request),
        "user_agent": str(request.META.get("HTTP_USER_AGENT", ""))[:300],
        "old_values": old_values,
        "new_values": new_values,
        "metadata": safe_metadata,
    }
    digest = _integrity_digest(payload)

    return AuditLog.objects.create(
        actor=actor,
        actor_username=actor_username,
        actor_role=actor_role,
        action=action,
        category=payload["category"],
        outcome=outcome,
        source=payload["source"],
        object_type=payload["object_type"],
        object_reference=payload["object_reference"],
        request_id=payload["request_id"],
        http_method=payload["http_method"],
        path=payload["path"],
        ip_address=payload["ip_address"],
        user_agent=payload["user_agent"],
        old_values=old_values,
        new_values=new_values,
        metadata=safe_metadata,
        integrity_hash=digest,
    )


def audit_failure(request, action, obj, *, metadata=None):
    return audit(
        request,
        action,
        obj,
        metadata=metadata,
        outcome=AuditLog.Outcome.FAILURE,
    )


def verify_integrity(log):
    if not log.integrity_hash:
        return None

    payload = {
        "actor_username": log.actor_username,
        "actor_role": log.actor_role,
        "action": log.action,
        "category": log.category,
        "outcome": log.outcome,
        "source": log.source,
        "object_type": log.object_type,
        "object_reference": log.object_reference,
        "request_id": log.request_id,
        "http_method": log.http_method,
        "path": log.path,
        "ip_address": str(log.ip_address) if log.ip_address else None,
        "user_agent": log.user_agent,
        "old_values": log.old_values,
        "new_values": log.new_values,
        "metadata": log.metadata,
    }
    expected = _integrity_digest(payload)
    return hmac.compare_digest(expected, log.integrity_hash or "")

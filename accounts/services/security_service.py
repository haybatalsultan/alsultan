import hashlib
import hmac
import ipaddress
import logging

from django.conf import settings

from accounts.models import SecurityEvent

log = logging.getLogger("haybat.security")


SENSITIVE_DETAIL_KEYS = {
    "password",
    "password1",
    "password2",
    "new_password1",
    "new_password2",
    "token",
    "secret",
    "cookie",
    "authorization",
}


def _valid_ip(value):
    """Return a canonical IP string or None. Never raises on attacker input."""
    value = (value or "").strip()
    if not value:
        return None
    # REMOTE_ADDR should not contain a port. Reject anything that is not a
    # syntactically valid IPv4/IPv6 address instead of trying to guess.
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def network_peer_ip(request):
    """
    Return the immediate TCP peer reported by the WSGI server.

    Security boundary:
    We intentionally do NOT trust CF-Connecting-IP or X-Forwarded-For here.
    On Render the peer is normally a Render/edge proxy, not the end user.
    That is acceptable for an audit *network-peer* field and for a coarse
    anti-abuse bucket. Authentication throttling must never rely on this value
    alone.
    """
    return _valid_ip(request.META.get("REMOTE_ADDR"))


def forwarded_ip_hint(request):
    """
    Parse a forwarded address only as an informational hint.

    The return value MUST NOT be used as the sole basis for authentication
    throttling, authorization, or audit attribution because forwarding headers
    can be attacker-controlled unless a trusted edge sanitizes them.
    """
    raw = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if not raw:
        return None

    # Keep the right-most syntactically valid value as a diagnostic hint.
    # We still explicitly mark it untrusted.
    for item in reversed(raw.split(",")):
        parsed = _valid_ip(item)
        if parsed:
            return parsed
    return None


def client_ip(request):
    """
    Backward-compatible alias.

    Historically this function trusted forwarded headers. It now returns the
    immediate network peer only. Do not reinterpret this as a verified end-user
    address when the app is behind Render or another reverse proxy.
    """
    return network_peer_ip(request)


def security_digest(label, value):
    """
    HMAC a security identifier before it is used in cache keys/log correlations.
    This prevents raw usernames/emails/session identifiers appearing in Redis.
    """
    normalized = str(value or "").strip().casefold()
    if not normalized:
        normalized = "unknown"
    material = f"{label}:{normalized}".encode("utf-8", "ignore")
    key = settings.SECRET_KEY.encode("utf-8", "ignore")
    return hmac.new(key, material, hashlib.sha256).hexdigest()[:32]


def record_event(request, event, user=None, **details):
    safe = {
        key: value
        for key, value in details.items()
        if key.casefold() not in SENSITIVE_DETAIL_KEYS
    }

    # Keep forwarded data out of the authoritative ip_address column. A short
    # hash can still help correlate repeated proxy hints without storing a
    # spoofable raw value as if it were verified identity.
    forwarded_hint = forwarded_ip_hint(request)
    if forwarded_hint:
        safe.setdefault(
            "forwarded_ip_hint_hash",
            security_digest("forwarded-ip-hint", forwarded_hint)[:16],
        )
        safe.setdefault("forwarded_ip_trusted", False)

    peer = network_peer_ip(request)
    SecurityEvent.objects.create(
        user=user if getattr(user, "pk", None) else None,
        event=event,
        ip_address=peer,
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        details=safe,
    )
    log.info("%s peer_ip=%s", event, peer or "unknown")

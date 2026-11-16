"""Privacy-preserving live product viewer counts backed by Django's cache.

Only a random per-session token is stored. No IP address, account id, email,
or other customer data is used for this storefront indicator.
"""

import secrets
import time

from django.core.cache import cache

VIEWER_WINDOW_SECONDS = 180
HEARTBEAT_MIN_SECONDS = 20
_LOCK_SECONDS = 3


def _presence_key(product_public_id):
    return f"product-viewers:v1:{product_public_id}"


def _heartbeat_key(product_public_id, viewer_token):
    return f"product-viewer-heartbeat:v1:{product_public_id}:{viewer_token}"


def _lock_key(product_public_id):
    return f"product-viewers-lock:v1:{product_public_id}"


def get_or_create_viewer_token(request):
    token = request.session.get("storefront_viewer_token")
    if not token:
        token = secrets.token_urlsafe(18)
        request.session["storefront_viewer_token"] = token
    return token


def touch_product_viewer(product_public_id, viewer_token):
    """Record one active browser session and return the approximate live count.

    Cache locking avoids lost updates across Gunicorn workers when Redis is used
    in production. The database is intentionally not written for this metric.
    """
    now = int(time.time())
    presence_key = _presence_key(product_public_id)
    heartbeat_key = _heartbeat_key(product_public_id, viewer_token)

    # Repeated polling/refreshes from the same browser do not inflate the count.
    if not cache.add(heartbeat_key, 1, timeout=HEARTBEAT_MIN_SECONDS):
        current = cache.get(presence_key, {})
        return _pruned_count(current, now)

    lock_key = _lock_key(product_public_id)
    if not cache.add(lock_key, 1, timeout=_LOCK_SECONDS):
        current = cache.get(presence_key, {})
        return _pruned_count(current, now)

    try:
        current = cache.get(presence_key, {})
        if not isinstance(current, dict):
            current = {}
        cutoff = now - VIEWER_WINDOW_SECONDS
        current = {
            token: int(last_seen)
            for token, last_seen in current.items()
            if isinstance(token, str)
            and isinstance(last_seen, (int, float))
            and int(last_seen) >= cutoff
        }
        current[viewer_token] = now
        cache.set(presence_key, current, timeout=VIEWER_WINDOW_SECONDS + 30)
        return len(current)
    finally:
        cache.delete(lock_key)


def _pruned_count(current, now):
    if not isinstance(current, dict):
        return 0
    cutoff = now - VIEWER_WINDOW_SECONDS
    return sum(
        1
        for token, last_seen in current.items()
        if isinstance(token, str)
        and isinstance(last_seen, (int, float))
        and int(last_seen) >= cutoff
    )

import logging

from django.conf import settings
from django.contrib.auth import logout
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect

from accounts.services.security_service import (
    network_peer_ip,
    record_event,
    security_digest,
)

security_log = logging.getLogger("haybat.security")


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import uuid

        request.request_id = uuid.uuid4().hex
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        response["Permissions-Policy"] = "geolocation=(self)"
        return response


class DefaultArabicLanguageMiddleware:
    """Force Arabic on first visit while respecting an explicit saved language choice."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cookie_name = settings.LANGUAGE_COOKIE_NAME
        if cookie_name not in request.COOKIES:
            request.COOKIES[cookie_name] = "ar"
        return self.get_response(request)


class SensitiveEndpointRateLimitMiddleware:
    """
    Multi-bucket throttling for sensitive POST endpoints.

    Security model:
    * Forwarded headers are never the sole identity.
    * Authentication endpoints always have a stable account/flow bucket.
    * A coarse immediate-peer bucket limits high-volume spraying even when an
      attacker rotates usernames/emails/forwarded headers.
    * X-Forwarded-For / CF-Connecting-IP are not used for throttling at all.
    * Production can fail closed when the shared rate-limit cache is unavailable.

    LIMITS values are (attempts, window_seconds).
    """

    LIMITS = {
        "/account/login/": (10, 300),
        "/account/register/": (6, 600),
        "/account/password-reset/": (5, 900),
        "/account/mfa/verify/": (8, 300),
        "/account/mfa/setup/": (8, 300),
        "/orders/checkout/": (20, 300),
        "/orders/track/": (12, 300),
        "/orders/cart/follow-up/": (8, 600),
        "/orders/cart/follow-up/cancel/": (8, 600),
        "/orders/cart/reservation-limit-request/": (4, 900),
        "/location/reverse/": (20, 600),
        "/accounts/google/login/": (20, 300),
        "/accounts/3rdparty/signup/": (10, 600),
    }

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _post_value(request, *names):
        for name in names:
            value = request.POST.get(name)
            if value:
                return str(value).strip()
        return ""

    def _stable_actor_material(self, request):
        path = request.path

        if path == "/account/login/":
            return "login-account", self._post_value(request, "username")

        if path == "/account/register/":
            value = self._post_value(request, "email") or self._post_value(
                request, "username"
            )
            return "registration-identity", value

        if path == "/account/password-reset/":
            return "password-reset-email", self._post_value(request, "email")

        if path in {"/account/mfa/verify/", "/account/mfa/setup/"}:
            preauth_id = request.session.get("preauth_user_id")
            user = getattr(request, "user", None)
            value = preauth_id or (
                str(user.pk) if user and user.is_authenticated else ""
            )
            return "mfa-flow-user", value

        if path == "/orders/checkout/":
            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                return "checkout-user", str(user.pk)
            value = self._post_value(request, "customer_email") or self._post_value(
                request, "customer_phone"
            )
            return "checkout-guest", value

        if path == "/orders/track/":
            value = "|".join(
                filter(
                    None,
                    (
                        self._post_value(request, "reference"),
                        self._post_value(request, "phone"),
                    ),
                )
            )
            return "order-track", value

        if path == "/orders/cart/reservation-limit-request/":
            user = getattr(request, "user", None)
            return "reservation-limit-user", str(
                user.pk
            ) if user and user.is_authenticated else "anonymous"

        if path.startswith("/orders/cart/follow-up"):
            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                return "cart-followup-user", str(user.pk)
            return "cart-followup-phone", self._post_value(
                request, "phone", "contact_phone", "customer_phone"
            )

        if path == "/location/reverse/":
            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                return "location-user", str(user.pk)

        # OAuth and remaining anonymous flows: use the existing session when
        # available. This is supplementary to the peer and forwarded-hint buckets.
        session_key = getattr(request.session, "session_key", None)
        if session_key:
            return "session", session_key

        return "path-anonymous", path

    @staticmethod
    def _increment(key, window):
        """
        Increment a fixed-window bucket without resetting its TTL on every hit.

        cache.add() is atomic for Redis/Valkey and Django's supported cache
        backends. If another request created the key first, incr() increments it.
        """
        if cache.add(key, 1, timeout=window):
            return 1
        return cache.incr(key)

    def _buckets(self, request, limit):
        label, actor_value = self._stable_actor_material(request)
        buckets = []

        # Stable account/flow identity: the main defense against XFF rotation.
        if actor_value:
            buckets.append(
                (
                    f"rl:v2:actor:{request.path}:{security_digest(label, actor_value)}",
                    limit,
                    "actor",
                )
            )

        # A network-peer bucket is useful for direct/local deployments but is
        # disabled in Render production because many users can share an edge
        # proxy address. Enabling it there would let one attacker cause a
        # collective lockout for unrelated customers.
        if getattr(settings, "RATE_LIMIT_USE_NETWORK_PEER", True):
            peer = network_peer_ip(request)
            if peer:
                buckets.append(
                    (
                        f"rl:v2:peer:{request.path}:{security_digest('peer', peer)}",
                        max(limit * 4, 25),
                        "peer",
                    )
                )

        # Existing authenticated/anonymous session, where available, adds a
        # second stable dimension without exposing the session key in Redis.
        session_key = getattr(request.session, "session_key", None)
        if session_key:
            buckets.append(
                (
                    f"rl:v2:session:{request.path}:{security_digest('session', session_key)}",
                    max(limit * 2, 10),
                    "session",
                )
            )

        return buckets

    def __call__(self, request):
        if request.method != "POST" or request.path not in self.LIMITS:
            return self.get_response(request)

        limit, window = self.LIMITS[request.path]

        try:
            for key, bucket_limit, bucket_name in self._buckets(request, limit):
                count = self._increment(key, window)
                if count > bucket_limit:
                    security_log.warning(
                        "rate_limit_exceeded path=%s bucket=%s request_id=%s",
                        request.path,
                        bucket_name,
                        getattr(request, "request_id", "unknown"),
                    )
                    response = JsonResponse(
                        {"detail": "Too many requests. Try again later."},
                        status=429,
                    )
                    response["Retry-After"] = str(window)
                    response["Cache-Control"] = "no-store"
                    return response
        except Exception:
            security_log.exception(
                "rate_limit_cache_error path=%s request_id=%s",
                request.path,
                getattr(request, "request_id", "unknown"),
            )
            if getattr(settings, "RATE_LIMIT_FAIL_CLOSED", False):
                response = JsonResponse(
                    {
                        "detail": "Security service temporarily unavailable. Try again shortly."
                    },
                    status=503,
                )
                response["Retry-After"] = "30"
                response["Cache-Control"] = "no-store"
                return response

        return self.get_response(request)


class ManagementMFAEnforcementMiddleware:
    """Defense in depth: every owner/supervisor management session requires MFA."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user
            and user.is_authenticated
            and getattr(user, "role", None) in {"OWNER", "SUPERVISOR"}
            and request.path.startswith("/management/")
        ):
            from accounts.services.mfa_service import mfa_enabled, session_mfa_verified

            if not mfa_enabled(user):
                return redirect("accounts:mfa_setup")
            if not session_mfa_verified(request, user):
                logout(request)
                return redirect("accounts:login")
        return self.get_response(request)


class ManagementSecurityAuditMiddleware:
    """Record denied management access without exposing request bodies or secrets."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/management/") and response.status_code == 403:
            try:
                record_event(
                    request,
                    "management_access_denied",
                    request.user
                    if getattr(request.user, "is_authenticated", False)
                    else None,
                    path=request.path[:300],
                    method=request.method[:10],
                    request_id=getattr(request, "request_id", ""),
                )
            except Exception:
                security_log.exception("unable_to_record_management_access_denied")
        return response

import base64
import time
from io import BytesIO

import qrcode
from django.contrib.auth import get_user_model

PREAUTH_TTL_SECONDS = 10 * 60


def mfa_enabled(user):
    if not getattr(user, "is_authenticated", False):
        return False
    device = getattr(user, "mfa_device", None)
    return bool(device and device.enabled)


def mark_mfa_verified(request, user):
    request.session["mfa_verified_user_id"] = str(user.pk)
    request.session["mfa_verified_at"] = int(time.time())


def session_mfa_verified(request, user):
    return mfa_enabled(user) and request.session.get("mfa_verified_user_id") == str(
        user.pk
    )


def begin_preauth(request, user, *, purpose, next_url=""):
    # Rotate the anonymous session as soon as the primary credential succeeds.
    request.session.cycle_key()
    request.session["preauth_user_id"] = user.pk
    request.session["preauth_purpose"] = purpose
    request.session["preauth_started_at"] = int(time.time())
    request.session["preauth_next"] = next_url
    # A new primary-authentication attempt must receive a fresh enrollment secret.
    request.session.pop("mfa_setup_secret_issued", None)
    request.session.pop("mfa_verified_user_id", None)
    request.session.pop("mfa_verified_at", None)


def clear_preauth(request):
    for key in (
        "preauth_user_id",
        "preauth_purpose",
        "preauth_started_at",
        "preauth_next",
        "mfa_setup_secret_issued",
    ):
        request.session.pop(key, None)


def get_preauth_user(request, *, purpose=None):
    uid = request.session.get("preauth_user_id")
    started = request.session.get("preauth_started_at")
    stored_purpose = request.session.get("preauth_purpose")
    if not uid or not started:
        clear_preauth(request)
        return None
    try:
        if int(time.time()) - int(started) > PREAUTH_TTL_SECONDS:
            clear_preauth(request)
            return None
    except (TypeError, ValueError):
        clear_preauth(request)
        return None
    if purpose and stored_purpose != purpose:
        return None
    return (
        get_user_model()
        .objects.filter(pk=uid, is_active=True, is_archived=False)
        .first()
    )


def provisioning_qr_data_uri(provisioning_uri):
    """Create the TOTP QR locally; the provisioning secret is never sent to a third party."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=7,
        border=4,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"

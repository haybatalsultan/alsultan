import pyotp
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST

from ambassadors.services.program import ensure_profile, settings_obj
from core.services.audit_service import audit
from orders.services.loyalty_service import loyalty_status_for_user

from .forms import (
    AddressForm,
    MFAVerifyForm,
    RegistrationForm,
    SecureAuthenticationForm,
)
from .models import MFADevice, User
from .services.mfa_service import (
    begin_preauth,
    clear_preauth,
    get_preauth_user,
    mark_mfa_verified,
    mfa_enabled,
    provisioning_qr_data_uri,
)
from .services.security_service import record_event

CORE_HOME_URL = 'core:home'
MANAGEMENT_DASHBOARD_URL = 'core:management_dashboard'
ACCOUNTS_LOGIN_URL = 'accounts:login'

LOCAL_AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"


def register(request):
    if request.user.is_authenticated:
        return redirect(CORE_HOME_URL)
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend=LOCAL_AUTH_BACKEND)
        request.session.cycle_key()
        record_event(request, "registration_success", user)
        if settings_obj().enabled:
            return redirect("ambassadors:account")
        return redirect(CORE_HOME_URL)
    return render(
        request,
        "accounts/register.html",
        {"form": form, "ambassador_program": settings_obj()},
    )


def login_view(request):
    if request.user.is_authenticated:
        if request.user.role in {User.Role.OWNER, User.Role.SUPERVISOR}:
            return redirect(MANAGEMENT_DASHBOARD_URL)
        return redirect(CORE_HOME_URL)

    form = SecureAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            candidate = request.GET.get("next", "")
            safe_next = (
                candidate
                if url_has_allowed_host_and_scheme(
                    candidate,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                )
                else ""
            )

            management_role = user.role in {User.Role.OWNER, User.Role.SUPERVISOR}
            if management_role and not mfa_enabled(user):
                begin_preauth(request, user, purpose="setup", next_url=safe_next)
                record_event(request, "management_mfa_enrollment_required", user)
                return redirect("accounts:mfa_setup")

            if mfa_enabled(user):
                begin_preauth(request, user, purpose="verify", next_url=safe_next)
                record_event(request, "mfa_challenge_started", user)
                return redirect("accounts:mfa_verify")

            login(request, user, backend=LOCAL_AUTH_BACKEND)
            request.session.cycle_key()
            record_event(request, "login_success", user)
            default_target = (
                MANAGEMENT_DASHBOARD_URL
                if user.role == User.Role.SUPERVISOR
                else CORE_HOME_URL
            )
            return redirect(safe_next or default_target)
        record_event(request, "login_failure")
    return render(request, "accounts/login.html", {"form": form})


@require_POST
@login_required
def logout_view(request):
    record_event(request, "logout", request.user)
    logout(request)
    return redirect(CORE_HOME_URL)


@login_required
def profile(request):
    address_initial = {}
    if request.method != "POST" and request.user.country:
        address_initial["country"] = request.user.country
    form = AddressForm(
        request.POST or None,
        initial=address_initial if request.method != "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        if obj.is_default:
            request.user.addresses.filter(is_default=True).update(is_default=False)
        obj.save()
        audit(
            request,
            "address_created",
            obj,
            new={
                "country": obj.country,
                "is_default": obj.is_default,
                # Deliberately do not place street/address coordinates in the
                # owner audit stream. The event records the change without
                # duplicating sensitive customer location data.
                "location_details_recorded": False,
            },
        )
        return redirect("accounts:profile")
    return render(
        request,
        "accounts/profile.html",
        {
            "address_form": form,
            "addresses": request.user.addresses.order_by("-is_default", "-created_at"),
            "loyalty": loyalty_status_for_user(request.user)
            if request.user.role == User.Role.CUSTOMER
            else None,
            "ambassador_program": settings_obj()
            if request.user.role == User.Role.CUSTOMER
            else None,
            "ambassador_profile": ensure_profile(request.user)
            if request.user.role == User.Role.CUSTOMER
            else None,
        },
    )


@never_cache
@sensitive_post_parameters("code")
def mfa_verify(request):
    user = get_preauth_user(request, purpose="verify")
    if not user or not mfa_enabled(user):
        clear_preauth(request)
        return redirect(ACCOUNTS_LOGIN_URL)

    form = MFAVerifyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if pyotp.TOTP(user.mfa_device.secret).verify(
            form.cleaned_data["code"], valid_window=1
        ):
            nxt = request.session.get("preauth_next", "")
            clear_preauth(request)
            login(request, user, backend=LOCAL_AUTH_BACKEND)
            request.session.cycle_key()
            mark_mfa_verified(request, user)
            record_event(request, "mfa_success", user)
            default_target = (
                MANAGEMENT_DASHBOARD_URL
                if user.role in {User.Role.OWNER, User.Role.SUPERVISOR}
                else CORE_HOME_URL
            )
            return redirect(nxt or default_target)
        record_event(request, "mfa_failure", user)
        form.add_error("code", "رمز التحقق غير صحيح.")
    return render(request, "accounts/mfa_verify.html", {"form": form})


@never_cache
@sensitive_post_parameters("code")
def mfa_setup(request):
    preauth_user = None
    if request.user.is_authenticated:
        user = request.user
        if user.role not in {User.Role.OWNER, User.Role.SUPERVISOR}:
            raise PermissionDenied
    else:
        preauth_user = get_preauth_user(request, purpose="setup")
        if not preauth_user or preauth_user.role not in {
            User.Role.OWNER,
            User.Role.SUPERVISOR,
        }:
            clear_preauth(request)
            return redirect(ACCOUNTS_LOGIN_URL)
        user = preauth_user

    device, _ = MFADevice.objects.get_or_create(
        user=user,
        defaults={"secret": pyotp.random_base32()},
    )

    # Enrollment secrets are one-time setup material. Each new management
    # pre-auth flow rotates any old, unconfirmed secret (including one that may have
    # been exposed in a screenshot) and keeps it stable only for this setup session.
    if preauth_user and not request.session.get("mfa_setup_secret_issued"):
        device.secret = pyotp.random_base32()
        device.enabled = False
        device.confirmed_at = None
        device.save(update_fields=["secret", "enabled", "confirmed_at"])
        request.session["mfa_setup_secret_issued"] = True
    elif not device.secret:
        device.secret = pyotp.random_base32()
        device.enabled = False
        device.confirmed_at = None
        device.save(update_fields=["secret", "enabled", "confirmed_at"])

    form = MFAVerifyForm(request.POST or None)
    if request.method == "POST" and not device.enabled and form.is_valid():
        if pyotp.TOTP(device.secret).verify(form.cleaned_data["code"], valid_window=1):
            device.enabled = True
            device.confirmed_at = timezone.now()
            device.save(update_fields=["enabled", "confirmed_at"])
            record_event(request, "mfa_enabled", user)

            if preauth_user:
                nxt = request.session.get("preauth_next", "")
                clear_preauth(request)
                login(request, user, backend=LOCAL_AUTH_BACKEND)
                request.session.cycle_key()
                mark_mfa_verified(request, user)
                record_event(request, "login_success_after_mfa_enrollment", user)
                return redirect(nxt or MANAGEMENT_DASHBOARD_URL)
            return redirect(
                MANAGEMENT_DASHBOARD_URL
                if user.role == User.Role.OWNER
                else "accounts:profile"
            )

        record_event(request, "mfa_setup_failure", user)
        form.add_error("code", "رمز التحقق غير صحيح.")

    uri = (
        pyotp.TOTP(device.secret).provisioning_uri(
            name=user.email or user.username,
            issuer_name="Haybat Al Sultan",
        )
        if not device.enabled
        else ""
    )
    qr_data_uri = provisioning_qr_data_uri(uri) if uri else ""
    return render(
        request,
        "accounts/mfa_setup.html",
        {
            "form": form,
            "secret": device.secret if not device.enabled else "",
            "qr_data_uri": qr_data_uri,
            "enabled": device.enabled,
            "mandatory_management_setup": bool(
                preauth_user and user.role in {User.Role.OWNER, User.Role.SUPERVISOR}
            ),
        },
    )


@require_POST
@never_cache
def mfa_cancel_setup(request):
    """Cancel an unfinished enrollment without leaving a reusable TOTP secret behind."""
    if request.user.is_authenticated:
        user = request.user
        if user.role not in {User.Role.OWNER, User.Role.SUPERVISOR}:
            raise PermissionDenied
        MFADevice.objects.filter(user=user, enabled=False).delete()
        record_event(request, "mfa_setup_cancelled", user)
        logout(request)  # Flushes the authenticated session.
        return redirect(ACCOUNTS_LOGIN_URL)

    user = get_preauth_user(request, purpose="setup")
    if user:
        MFADevice.objects.filter(user=user, enabled=False).delete()
        record_event(request, "mfa_setup_cancelled", user)
    # Flush the entire anonymous pre-auth session, not just selected keys.
    request.session.flush()
    return redirect(ACCOUNTS_LOGIN_URL)

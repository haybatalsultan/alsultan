from django.core.exceptions import PermissionDenied

from .mfa_service import mfa_enabled

OWNER_ONLY_PRICING = {
    "cost_price",
    "selling_price",
    "discount_price",
    "pricing",
    "profit",
    "margin",
}


def require_owner(user):
    if not user.is_authenticated or user.role != "OWNER":
        raise PermissionDenied("Owner access required.")
    if not mfa_enabled(user):
        raise PermissionDenied("Owner MFA required.")
    return True


def can(user, permission):
    if not user.is_authenticated:
        return False
    if user.role == "OWNER":
        return mfa_enabled(user)
    if user.role != "SUPERVISOR":
        return False
    perms = getattr(user, "supervisor_permissions", None)
    return bool(perms and getattr(perms, permission, False))


def require_permission(user, permission):
    if permission in OWNER_ONLY_PRICING:
        return require_owner(user)
    if not can(user, permission):
        raise PermissionDenied("Permission denied.")
    return True


def assert_owner_integrity(actor, target, requested_role=None):
    if target.role == "OWNER" and (not actor.is_authenticated or actor.role != "OWNER"):
        raise PermissionDenied("Owner account is protected.")
    if requested_role == "OWNER" and actor.role != "OWNER":
        raise PermissionDenied("Only owner may perform owner-only provisioning.")

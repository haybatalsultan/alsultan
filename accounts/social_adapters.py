import uuid

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import PermissionDenied

from .models import User


class HaybatSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Security policy for third-party logins:
    - Google is customer-only.
    - Never allow Google to become an authentication path for OWNER/SUPERVISOR.
    - Never auto-match an existing local account by email (settings enforce this).
    """

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.role = User.Role.CUSTOMER

        # Our custom User still has AbstractUser.username. Keep Google signup
        # friction low by generating a server-side unique internal username.
        if not getattr(user, "username", ""):
            user.username = f"google_{uuid.uuid4().hex[:24]}"
        return user

    def pre_social_login(self, request, sociallogin):
        # Defense in depth: privileged users cannot connect/use social login.
        current = getattr(request, "user", None)
        if (
            current
            and current.is_authenticated
            and getattr(current, "role", None)
            in {User.Role.OWNER, User.Role.SUPERVISOR}
        ):
            raise PermissionDenied(
                "Social login is not available for privileged accounts."
            )

        existing_user = getattr(getattr(sociallogin, "account", None), "user", None)
        if (
            getattr(sociallogin, "is_existing", False)
            and existing_user
            and getattr(existing_user, "role", None) != User.Role.CUSTOMER
        ):
            raise PermissionDenied("Social login is restricted to customer accounts.")

        return super().pre_social_login(request, sociallogin)

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        if user.role != User.Role.CUSTOMER:
            user.role = User.Role.CUSTOMER
            user.save(update_fields=["role"])
        return user

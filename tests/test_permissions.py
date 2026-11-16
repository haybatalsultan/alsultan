from django.core.exceptions import PermissionDenied
from django.test import TestCase

from accounts.models import SupervisorPermission, User
from accounts.services.permission_service import require_permission


class PermissionTests(TestCase):
    def test_owner_only_pricing(self):
        s = User.objects.create_user("s", role="SUPERVISOR")
        SupervisorPermission.objects.create(user=s, edit_products=True)
        with self.assertRaises(PermissionDenied):
            require_permission(s, "cost_price")

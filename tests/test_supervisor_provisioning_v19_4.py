from django.test import TestCase
from django.urls import reverse

from accounts.forms import SupervisorCreateForm
from accounts.models import MFADevice, SupervisorPermission, User


class SupervisorProvisioningV194Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "owner-supervisor-v194",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        MFADevice.objects.create(
            user=self.owner,
            secret="JBSWY3DPEHPK3PXP",
            enabled=True,
        )

    def _owner_login(self):
        self.client.login(
            username="owner-supervisor-v194",
            password="VeryStrongPass!123",
        )
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session.save()

    def _valid_payload(self, **extra):
        payload = {
            "username": "new-supervisor-v194",
            "email": "supervisor-v194@example.com",
            "first_name": "Test",
            "last_name": "Supervisor",
            "country": "AE",
            "phone_local": "+971505939001",
            "password1": "AnotherStrongPass!987",
            "password2": "AnotherStrongPass!987",
        }
        payload.update(extra)
        return payload

    def test_supervisor_form_accepts_valid_uae_e164_number(self):
        form = SupervisorCreateForm(data=self._valid_payload())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["phone_e164_normalized"],
            "+971505939001",
        )

    def test_supervisor_form_rejects_phone_country_mismatch(self):
        form = SupervisorCreateForm(data=self._valid_payload(country="SA"))
        self.assertFalse(form.is_valid())
        self.assertIn("phone_local", form.errors)

    def test_supervisor_creation_redirects_to_separate_permissions_step(self):
        self._owner_login()
        response = self.client.post(
            reverse("core:management_supervisor_create"),
            self._valid_payload(),
        )
        supervisor = User.objects.get(username="new-supervisor-v194")

        self.assertRedirects(
            response,
            reverse(
                "core:management_supervisor_permissions",
                args=[supervisor.public_id],
            ),
            fetch_redirect_response=False,
        )

        permissions = supervisor.supervisor_permissions
        for field in permissions._meta.fields:
            if field.name in {"id", "user", "updated_at"}:
                continue
            self.assertFalse(
                getattr(permissions, field.name),
                f"{field.name} must default to False",
            )

    def test_forged_permissions_on_account_creation_are_ignored(self):
        self._owner_login()
        payload = self._valid_payload(
            username="forged-supervisor-v194",
            email="forged-v194@example.com",
            view_orders="on",
            mark_paid="on",
            edit_products="on",
        )
        response = self.client.post(
            reverse("core:management_supervisor_create"),
            payload,
        )
        self.assertEqual(response.status_code, 302)

        supervisor = User.objects.get(username="forged-supervisor-v194")
        permissions = supervisor.supervisor_permissions
        self.assertFalse(permissions.view_orders)
        self.assertFalse(permissions.mark_paid)
        self.assertFalse(permissions.edit_products)

    def test_permissions_page_is_owner_only(self):
        supervisor = User.objects.create_user(
            "target-supervisor-v194",
            password="VeryStrongPass!123",
            role=User.Role.SUPERVISOR,
        )
        SupervisorPermission.objects.create(user=supervisor)

        customer = User.objects.create_user(
            "customer-v194",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )
        self.client.login(
            username="customer-v194",
            password="VeryStrongPass!123",
        )
        response = self.client.get(
            reverse(
                "core:management_supervisor_permissions",
                args=[supervisor.public_id],
            )
        )
        self.assertEqual(response.status_code, 403)

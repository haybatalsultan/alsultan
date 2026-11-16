from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from core.models import StoreSetting
from orders.forms import CheckoutForm
from tests.helpers import login_management


class CheckoutFieldConfigurationTests(TestCase):
    def test_configurable_field_can_be_required_server_side(self):
        form = CheckoutForm(
            data={
                "customer_name": "Buyer",
                "customer_email": "",
                "country": "AE",
                "customer_phone": "0501234567",
                "area": "Abu Dhabi",
                "policy_acceptance": "on",
                "idempotency_key": "safe-key",
            },
            checkout_field_config={
                "customer_email": {"visible": True, "required": True}
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("customer_email", form.errors)

    def test_hidden_field_is_removed_and_cannot_be_forced_required(self):
        form = CheckoutForm(
            checkout_field_config={
                "city": {"visible": False, "required": True},
            }
        )
        self.assertNotIn("city", form.fields)

    def test_system_required_fields_cannot_be_removed_by_configuration(self):
        form = CheckoutForm(
            checkout_field_config={
                "customer_name": {"visible": False, "required": False},
                "customer_phone": {"visible": False, "required": False},
                "country": {"visible": False, "required": False},
                "area": {"visible": False, "required": False},
            }
        )
        for name in ("customer_name", "customer_phone", "country", "area"):
            self.assertIn(name, form.fields)
            self.assertTrue(form.fields[name].required)


class OwnerCheckoutFieldSettingsSecurityTests(TestCase):
    def setUp(self):
        self.owner_password = "StrongPass!123"
        self.owner = User.objects.create_user(
            "checkout-settings-owner",
            password=self.owner_password,
            role=User.Role.OWNER,
        )
        self.supervisor_password = "StrongPass!123"
        self.supervisor = User.objects.create_user(
            "checkout-settings-supervisor",
            password=self.supervisor_password,
            role=User.Role.SUPERVISOR,
        )

    def test_owner_can_update_whitelisted_checkout_fields(self):
        login_management(self.client, self.owner, self.owner_password)
        response = self.client.post(
            reverse("core:management_checkout_field_settings"),
            {
                "customer_email_visible": "on",
                "customer_email_required": "on",
                "emirate_visible": "on",
                "city_visible": "on",
                "street_visible": "on",
                "building_visible": "on",
                "apartment_or_villa_visible": "on",
                "postal_code_visible": "on",
                "additional_notes_visible": "on",
                # Untrusted/non-whitelisted keys must be ignored.
                "customer_name_visible": "",
                "customer_name_required": "",
                "policy_acceptance_required": "",
                "idempotency_key_visible": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        setting = StoreSetting.objects.get(singleton=True)
        self.assertTrue(setting.checkout_field_config["customer_email"]["visible"])
        self.assertTrue(setting.checkout_field_config["customer_email"]["required"])
        self.assertNotIn("customer_name", setting.checkout_field_config)
        self.assertNotIn("policy_acceptance", setting.checkout_field_config)
        self.assertNotIn("idempotency_key", setting.checkout_field_config)

    def test_supervisor_cannot_open_owner_checkout_settings(self):
        login_management(self.client, self.supervisor, self.supervisor_password)
        response = self.client.get(reverse("core:management_checkout_field_settings"))
        self.assertEqual(response.status_code, 403)


class StoreSettingCheckoutFieldDefaultRegressionTests(TestCase):
    def test_store_setting_can_be_created_without_explicit_checkout_config(self):
        setting = StoreSetting.objects.create(singleton=True)
        self.assertIsInstance(setting.checkout_field_config, dict)
        self.assertIn("customer_email", setting.checkout_field_config)
        self.assertTrue(setting.checkout_field_config["customer_email"]["visible"])
        self.assertFalse(setting.checkout_field_config["customer_email"]["required"])

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from accounts.forms import AddressForm
from accounts.models import User
from core.countries import address_country_choices, country_choices, normalize_phone


class GlobalCountryAndPhoneTests(SimpleTestCase):
    def test_country_list_is_global(self):
        choices = dict(address_country_choices("en"))
        self.assertGreaterEqual(len(choices), 240)
        for code in ("AE", "SA", "US", "GB", "JP", "BR", "ZA", "AU"):
            self.assertIn(code, choices)

    def test_address_country_labels_do_not_include_phone_prefix(self):
        choices = dict(address_country_choices("en"))
        self.assertNotIn("+971", choices["AE"])

    def test_registration_country_labels_include_calling_prefix(self):
        choices = dict(country_choices("en"))
        self.assertIn("+971", choices["AE"])
        self.assertIn("+44", choices["GB"])

    def test_phone_normalization_uses_international_metadata(self):
        self.assertEqual(normalize_phone("AE", "0501234567"), "+971501234567")
        self.assertEqual(normalize_phone("GB", "020 8366 1177"), "+442083661177")

    def test_phone_country_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_phone("AE", "+442083661177")


class AddressCoordinateValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="location-user",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )

    def test_address_rejects_latitude_outside_world_bounds(self):
        form = AddressForm(
            data={
                "label": "Home",
                "country": "AE",
                "emirate": "Abu Dhabi",
                "city": "Abu Dhabi",
                "area": "Al Danah",
                "street": "",
                "building": "",
                "apartment_or_villa": "",
                "postal_code": "",
                "additional_notes": "",
                "latitude": "91.000000",
                "longitude": "54.377300",
                "is_default": False,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("latitude", form.errors)

    def test_address_rejects_longitude_outside_world_bounds(self):
        form = AddressForm(
            data={
                "label": "Home",
                "country": "US",
                "emirate": "California",
                "city": "Los Angeles",
                "area": "Downtown",
                "street": "",
                "building": "",
                "apartment_or_villa": "",
                "postal_code": "",
                "additional_notes": "",
                "latitude": "34.052235",
                "longitude": "181.000000",
                "is_default": False,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("longitude", form.errors)


@override_settings(GOOGLE_MAPS_API_KEY="browser-test-key")
class LocationTemplateSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="maps-user",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )

    def test_profile_receives_browser_key_only_as_page_configuration(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-google-maps-key="browser-test-key"')
        self.assertContains(response, "استخدام موقعي الحالي")

    def test_location_form_remains_normal_post_save(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:profile"))
        self.assertContains(response, 'method="post"')
        self.assertContains(response, "csrfmiddlewaretoken")


class MapsCSPTests(SimpleTestCase):
    def test_maps_hosts_are_scoped_to_required_csp_directives(self):
        from django.conf import settings

        self.assertIn("https://maps.googleapis.com", settings.SECURE_CSP["script-src"])
        self.assertIn("https://maps.googleapis.com", settings.SECURE_CSP["connect-src"])
        self.assertIn("https://maps.gstatic.com", settings.SECURE_CSP["script-src"])
        self.assertNotIn(
            "https://maps.googleapis.com", settings.SECURE_CSP["form-action"]
        )

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.forms import RegistrationForm
from accounts.models import Address, User
from catalog.models import Category, Product
from core.countries import normalize_phone
from orders.models import Cart, CartItem, Order


class CountryAndPhoneTests(TestCase):
    def test_registration_normalizes_uae_phone(self):
        form = RegistrationForm(
            data={
                "username": "country-user",
                "email": "country@example.com",
                "first_name": "Country",
                "last_name": "User",
                "country": "AE",
                "phone_local": "050 123 4567",
                "password1": "VeryStrongPass!123",
                "password2": "VeryStrongPass!123",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.country, "AE")
        self.assertEqual(user.phone_e164, "+971501234567")

    def test_phone_country_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            normalize_phone("AE", "+966501234567")


class SavedAddressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="address-user",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )

    def test_profile_keeps_only_one_default_address(self):
        self.client.login(username="address-user", password="VeryStrongPass!123")
        first = Address.objects.create(
            user=self.user,
            label="Home",
            country="AE",
            emirate="Abu Dhabi",
            city="Abu Dhabi",
            area="Khalifa City",
            is_default=True,
        )
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "label": "Work",
                "country": "AE",
                "emirate": "Abu Dhabi",
                "city": "Abu Dhabi",
                "area": "Mussafah",
                "street": "",
                "building": "",
                "apartment_or_villa": "",
                "postal_code": "",
                "additional_notes": "",
                "latitude": "",
                "longitude": "",
                "is_default": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        first.refresh_from_db()
        self.assertFalse(first.is_default)
        self.assertEqual(
            Address.objects.filter(user=self.user, is_default=True).count(), 1
        )


class GuestCheckoutTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            name_ar="مسابيح ضيف", name_en="Guest Misbah", slug="guest-misbah"
        )
        self.product = Product.objects.create(
            name_ar="مسبحة ضيف",
            name_en="Guest Product",
            category=category,
            cost_price=Decimal(10),
            selling_price=Decimal(100),
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )

    def test_checkout_page_explicitly_allows_guest(self):
        cart = Cart.objects.create(session_key="guest-session")
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        session = self.client.session
        session.save()
        # Let cart service establish the browser cart, then add normally.
        self.client.post(
            reverse("orders:cart_add", args=[self.product.public_id]), {"quantity": 1}
        )
        response = self.client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "الشراء كضيف")
        key = response.context["idempotency_key"]
        self.assertTrue(key)
        self.assertContains(response, f'value="{key}"')

    def test_guest_can_create_order_without_account(self):
        self.client.post(
            reverse("orders:cart_add", args=[self.product.public_id]), {"quantity": 1}
        )
        get_response = self.client.get(reverse("orders:checkout"))
        key = get_response.context["idempotency_key"]
        response = self.client.post(
            reverse("orders:checkout"),
            {
                "idempotency_key": key,
                "customer_name": "Guest Customer",
                "customer_email": "",
                "country": "AE",
                "customer_phone": "0501234567",
                "emirate": "Abu Dhabi",
                "city": "Abu Dhabi",
                "area": "Khalifa City",
                "street": "",
                "building": "",
                "apartment_or_villa": "",
                "postal_code": "",
                "additional_notes": "",
                "latitude": "",
                "longitude": "",
                "policy_acceptance": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(customer_name="Guest Customer")
        self.assertIsNone(order.user_id)
        self.assertEqual(order.customer_phone, "+971501234567")


@override_settings(GOOGLE_MAPS_GEOCODING_API_KEY="test-key")
class ReverseGeocodingSecurityTests(TestCase):
    @patch("core.views.reverse_geocode")
    def test_reverse_geocode_is_post_only_and_returns_safe_fields(self, reverse_mock):
        self.assertEqual(
            self.client.get(reverse("core:reverse_geocode_location")).status_code, 405
        )
        reverse_mock.return_value = {
            "latitude": "24.453900",
            "longitude": "54.377300",
            "country": "AE",
            "emirate": "Abu Dhabi",
            "city": "Abu Dhabi",
            "area": "Al Danah",
            "street": "Example Street",
            "postal_code": "",
            "formatted_address": "Abu Dhabi, UAE",
        }
        response = self.client.post(
            reverse("core:reverse_geocode_location"),
            {
                "latitude": "24.4539",
                "longitude": "54.3773",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["country"], "AE")

    def test_invalid_coordinates_are_rejected_before_provider_call(self):
        response = self.client.post(
            reverse("core:reverse_geocode_location"),
            {
                "latitude": "999",
                "longitude": "54",
            },
        )
        self.assertEqual(response.status_code, 400)

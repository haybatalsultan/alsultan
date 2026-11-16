import re

from django import forms
from django.utils.translation import get_language

from core.countries import country_choices, normalize_phone
from core.services.checkout_fields import (
    CONFIGURABLE_CHECKOUT_FIELDS,
    sanitise_checkout_field_config,
)


MOBILE_NUMBER_EN = 'Mobile number'
MOBILE_NUMBER_AR = 'رقم الهاتف'

class CheckoutForm(forms.Form):
    customer_name = forms.CharField(max_length=180)
    customer_email = forms.EmailField(required=False)
    country = forms.ChoiceField()
    customer_phone = forms.CharField(max_length=24)
    emirate = forms.CharField(max_length=80, required=False)
    city = forms.CharField(max_length=120, required=False)
    area = forms.CharField(max_length=120)
    street = forms.CharField(max_length=160, required=False)
    building = forms.CharField(max_length=120, required=False)
    apartment_or_villa = forms.CharField(max_length=120, required=False)
    postal_code = forms.CharField(max_length=24, required=False)
    additional_notes = forms.CharField(
        max_length=500, required=False, widget=forms.Textarea
    )
    latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        min_value=-90,
        max_value=90,
        widget=forms.HiddenInput(attrs={"data-location-field": "latitude"}),
    )
    longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        min_value=-180,
        max_value=180,
        widget=forms.HiddenInput(attrs={"data-location-field": "longitude"}),
    )
    ambassador_code = forms.CharField(max_length=16, required=False)
    ambassador_discount_points = forms.IntegerField(required=False, min_value=0)
    policy_acceptance = forms.BooleanField(required=True)
    idempotency_key = forms.CharField(max_length=100, widget=forms.HiddenInput)

    def __init__(self, *args, checkout_field_config=None, **kwargs):
        super().__init__(*args, **kwargs)
        ar = get_language() != "en"
        checkout_field_config = sanitise_checkout_field_config(checkout_field_config)
        for name in CONFIGURABLE_CHECKOUT_FIELDS:
            options = checkout_field_config[name]
            if not options["visible"]:
                self.fields.pop(name, None)
                continue
            self.fields[name].required = options["required"]
        self.fields["country"].choices = country_choices("ar" if ar else "en")
        labels = {
            "customer_name": "الاسم الكامل" if ar else "Full name",
            "customer_email": "البريد الإلكتروني" if ar else "Email",
            "customer_phone": MOBILE_NUMBER_AR if ar else MOBILE_NUMBER_EN,
            "country": "الدولة وكود الاتصال" if ar else "Country & calling code",
            "emirate": "الإمارة / المنطقة" if ar else "Emirate / Region",
            "city": "المدينة" if ar else "City",
            "area": "المنطقة / الحي" if ar else "Area / District",
            "street": "الشارع" if ar else "Street",
            "building": "المبنى" if ar else "Building",
            "apartment_or_villa": "الشقة / الفيلا" if ar else "Apartment / Villa",
            "postal_code": "الرمز البريدي" if ar else "Postal code",
            "additional_notes": "ملاحظات التوصيل" if ar else "Delivery notes",
            "ambassador_code": "رمز سفير هيبة السلطان (اختياري)"
            if ar
            else "Haybat Alsultan Ambassador code (optional)",
            "ambassador_discount_points": "استخدام نقاط السفير كخصم (اختياري)"
            if ar
            else "Use ambassador points as discount (optional)",
            "policy_acceptance": "أوافق على الشروط وسياسة الاسترجاع."
            if ar
            else "I agree to the Terms and Returns Policy.",
            "idempotency_key": "",
        }
        for name, label in labels.items():
            if name not in self.fields:
                continue
            if (
                name in CONFIGURABLE_CHECKOUT_FIELDS
                and not self.fields[name].required
            ):
                label = f"{label} (اختياري)" if ar else f"{label} (optional)"
            self.fields[name].label = label
        for name, field in self.fields.items():
            if not field.widget.is_hidden and name != "policy_acceptance":
                field.widget.attrs["class"] = (
                    field.widget.attrs.get("class", "") + " form-control"
                ).strip()
        self.fields["country"].widget.attrs.update(
            {"data-country-select": "1", "data-address-field": "country"}
        )
        self.fields["customer_phone"].widget.attrs.update(
            {"autocomplete": "tel", "inputmode": "tel", "data-phone-input": "1"}
        )
        self.fields["ambassador_code"].widget.attrs.update(
            {"autocomplete": "off", "dir": "ltr", "placeholder": "HSA-XXXXXXXX"}
        )
        self.fields["ambassador_discount_points"].widget.attrs.update(
            {"inputmode": "numeric", "step": "1000", "min": "0", "placeholder": "1000"}
        )
        for name in ("emirate", "city", "area", "street", "postal_code"):
            if name in self.fields:
                self.fields[name].widget.attrs["data-address-field"] = name

    def clean(self):
        cleaned = super().clean()
        country = cleaned.get("country")
        phone = cleaned.get("customer_phone")
        if country and phone:
            try:
                cleaned["customer_phone"] = normalize_phone(country, phone)
            except ValueError:
                self.add_error(
                    "customer_phone",
                    "رقم الهاتف لا يطابق الدولة المختارة."
                    if get_language() != "en"
                    else "The phone number does not match the selected country.",
                )
        code = (cleaned.get("ambassador_code") or "").strip().upper()
        if code and not re.fullmatch(r"HSA-[A-Z2-9]{8}", code):
            self.add_error(
                "ambassador_code",
                "رمز السفير غير صالح."
                if get_language() != "en"
                else "Invalid ambassador code.",
            )
        cleaned["ambassador_code"] = code
        points = cleaned.get("ambassador_discount_points") or 0
        if points and points % 1000 != 0:
            self.add_error(
                "ambassador_discount_points",
                "يجب استخدام النقاط بمضاعفات 1000 نقطة."
                if get_language() != "en"
                else "Points must be used in blocks of 1,000.",
            )
        lat, lng = cleaned.get("latitude"), cleaned.get("longitude")
        if (lat is None) ^ (lng is None):
            raise forms.ValidationError(
                "إحداثيات الموقع غير مكتملة."
                if get_language() != "en"
                else "Location coordinates are incomplete."
            )

        for name in (
            "customer_name",
            "customer_email",
            "emirate",
            "city",
            "area",
            "street",
            "building",
            "apartment_or_villa",
            "postal_code",
            "additional_notes",
        ):
            if isinstance(cleaned.get(name), str):
                cleaned[name] = cleaned[name].strip()

        return cleaned


class OrderTrackingForm(forms.Form):
    reference = forms.RegexField(regex=r"^HS-[A-Z0-9-]{6,28}$", max_length=32)
    phone = forms.RegexField(regex=r"^\+[1-9]\d{7,14}$", max_length=16)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if get_language() == "en":
            self.fields["reference"].label = "Order reference"
            self.fields["phone"].label = MOBILE_NUMBER_EN
        else:
            self.fields["reference"].label = "رقم الطلب"
            self.fields["phone"].label = MOBILE_NUMBER_AR
        self.fields["reference"].widget.attrs.update(
            {
                "class": "form-control",
                "dir": "ltr",
                "autocomplete": "off",
                "placeholder": "HS-260822-XXXXXX",
            }
        )
        self.fields["phone"].widget.attrs.update(
            {
                "class": "form-control",
                "dir": "ltr",
                "autocomplete": "tel",
                "inputmode": "tel",
                "placeholder": "+9715XXXXXXXX",
            }
        )


class CartFollowUpForm(forms.Form):
    phone = forms.RegexField(regex=r"^\+[1-9]\d{7,14}$", max_length=16)
    whatsapp_opt_in = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if get_language() == "en":
            self.fields["phone"].label = MOBILE_NUMBER_EN
            self.fields[
                "whatsapp_opt_in"
            ].label = "I agree to receive one WhatsApp reminder about this cart if I do not complete my order."
        else:
            self.fields["phone"].label = MOBILE_NUMBER_AR
            self.fields[
                "whatsapp_opt_in"
            ].label = "أوافق على استلام تذكير واحد عبر واتساب بخصوص هذه السلة إذا لم أكمل الطلب."

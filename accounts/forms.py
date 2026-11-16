from typing import ClassVar

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import get_language

from core.countries import address_country_choices, country_choices, normalize_phone

from .models import Address, User

USERNAME_LABEL_AR = "اسم المستخدم"
PASSCODE_LABEL_AR = "كلمة المرور"


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    country = forms.ChoiceField()
    phone_local = forms.CharField(max_length=24, required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "country",
            "phone_local",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ar = get_language() != "en"
        self.fields["country"].choices = country_choices("ar" if ar else "en")
        self.fields["country"].initial = "AE"
        labels = {
            "username": USERNAME_LABEL_AR if ar else "Username",
            "email": "البريد الإلكتروني" if ar else "Email",
            "first_name": "الاسم الأول" if ar else "First name",
            "last_name": "اسم العائلة" if ar else "Last name",
            "country": "الدولة وكود الاتصال" if ar else "Country & calling code",
            "phone_local": "رقم الهاتف" if ar else "Mobile number",
            "password1": PASSCODE_LABEL_AR if ar else "Password",
            "password2": "تأكيد كلمة المرور" if ar else "Confirm password",
        }
        for name, label in labels.items():
            if name in self.fields:
                self.fields[name].label = label
                existing = self.fields[name].widget.attrs.get("class", "")
                self.fields[name].widget.attrs["class"] = (
                    existing + " form-control"
                ).strip()
        self.fields["country"].widget.attrs["data-country-select"] = "1"
        self.fields["phone_local"].widget.attrs.update(
            {
                "autocomplete": "tel",
                "inputmode": "tel",
                "data-phone-input": "1",
            }
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "هذا البريد الإلكتروني مستخدم بالفعل."
                if get_language() != "en"
                else "An account with this email already exists."
            )
        return email

    def clean(self):
        cleaned = super().clean()
        country = cleaned.get("country")
        phone = cleaned.get("phone_local")
        if country and phone:
            try:
                cleaned["phone_e164_normalized"] = normalize_phone(country, phone)
            except ValueError:
                self.add_error(
                    "phone_local",
                    (
                        "رقم الهاتف لا يطابق الدولة المختارة."
                        if get_language() != "en"
                        else "The phone number does not match the selected country."
                    ),
                )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CUSTOMER
        user.email = self.cleaned_data["email"]
        user.country = self.cleaned_data["country"]
        user.phone_e164 = self.cleaned_data["phone_e164_normalized"]
        if commit:
            user.save()
        return user


class SecureAuthenticationForm(AuthenticationForm):
    error_messages: ClassVar[dict[str, str]] = {
        "invalid_login": "Unable to sign in with the provided credentials.",
        "inactive": "Unable to sign in with the provided credentials.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ar = get_language() != "en"
        self.fields["username"].label = USERNAME_LABEL_AR if ar else "Username"
        self.fields["password"].label = PASSCODE_LABEL_AR if ar else "Password"


class AddressForm(forms.ModelForm):
    country = forms.ChoiceField()

    class Meta:
        model = Address
        fields = (
            "label",
            "country",
            "emirate",
            "city",
            "area",
            "street",
            "building",
            "apartment_or_villa",
            "postal_code",
            "additional_notes",
            "latitude",
            "longitude",
            "is_default",
        )
        widgets: ClassVar[dict[str, object]] = {
            "latitude": forms.HiddenInput(attrs={"data-location-field": "latitude"}),
            "longitude": forms.HiddenInput(attrs={"data-location-field": "longitude"}),
            "additional_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ar = get_language() != "en"
        self.fields["country"].choices = address_country_choices("ar" if ar else "en")
        labels = {
            "label": "اسم العنوان" if ar else "Address label",
            "country": "الدولة" if ar else "Country",
            "emirate": "الإمارة / المنطقة" if ar else "Emirate / Region",
            "city": "المدينة" if ar else "City",
            "area": "المنطقة / الحي" if ar else "Area / District",
            "street": "الشارع" if ar else "Street",
            "building": "المبنى" if ar else "Building",
            "apartment_or_villa": "الشقة / الفيلا" if ar else "Apartment / Villa",
            "postal_code": "الرمز البريدي" if ar else "Postal code",
            "additional_notes": "ملاحظات إضافية" if ar else "Additional notes",
            "latitude": "خط العرض" if ar else "Latitude",
            "longitude": "خط الطول" if ar else "Longitude",
            "is_default": "العنوان الافتراضي" if ar else "Default address",
        }
        for name, label in labels.items():
            if name in self.fields:
                self.fields[name].label = label
                if not self.fields[name].widget.is_hidden:
                    existing = self.fields[name].widget.attrs.get("class", "")
                    self.fields[name].widget.attrs["class"] = (
                        existing + " form-control"
                    ).strip()
        for name in ("country", "emirate", "city", "area", "street", "postal_code"):
            if name in self.fields:
                self.fields[name].widget.attrs["data-address-field"] = name
        self.fields["country"].widget.attrs["data-country-select"] = "1"

    def clean(self):
        cleaned = super().clean()
        lat, lng = cleaned.get("latitude"), cleaned.get("longitude")
        if (lat is None) ^ (lng is None):
            raise forms.ValidationError(
                "يجب حفظ إحداثيات الموقع كاملة."
                if get_language() != "en"
                else "Both latitude and longitude are required together."
            )
        if lat is not None and not (-90 <= lat <= 90):
            self.add_error(
                "latitude",
                (
                    "إحداثيات خط العرض غير صالحة."
                    if get_language() != "en"
                    else "Invalid latitude."
                ),
            )
        if lng is not None and not (-180 <= lng <= 180):
            self.add_error(
                "longitude",
                (
                    "إحداثيات خط الطول غير صالحة."
                    if get_language() != "en"
                    else "Invalid longitude."
                ),
            )

        # Normalize user-editable address text; it remains untrusted and template-autoescaped.
        for name in (
            "label",
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


class MFAVerifyForm(forms.Form):
    code = forms.RegexField(regex=r"^\d{6}$", max_length=6, min_length=6)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["code"].label = (
            "رمز التحقق" if get_language() != "en" else "Verification code"
        )


class SupervisorCreateForm(UserCreationForm):
    email = forms.EmailField(required=True)
    country = forms.ChoiceField()
    phone_local = forms.CharField(max_length=24, required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "country",
            "phone_local",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ar = get_language() != "en"

        self.fields["country"].choices = country_choices("ar" if ar else "en")
        self.fields["country"].initial = "AE"

        labels = {
            "username": USERNAME_LABEL_AR if ar else "Username",
            "email": "البريد الإلكتروني" if ar else "Email",
            "first_name": "الاسم الأول" if ar else "First name",
            "last_name": "اسم العائلة" if ar else "Last name",
            "country": "الدولة وكود الاتصال" if ar else "Country & calling code",
            "phone_local": "رقم الهاتف" if ar else "Mobile number",
            "password1": PASSCODE_LABEL_AR if ar else "Password",
            "password2": "تأكيد كلمة المرور" if ar else "Confirm password",
        }
        for name, label in labels.items():
            self.fields[name].label = label
            existing = self.fields[name].widget.attrs.get("class", "")
            self.fields[name].widget.attrs["class"] = (
                existing + " management-input"
            ).strip()

        self.fields["country"].widget.attrs["data-country-select"] = "1"
        self.fields["phone_local"].widget.attrs.update(
            {
                "autocomplete": "tel",
                "inputmode": "tel",
                "data-phone-input": "1",
                "placeholder": "+971501234567",
                "dir": "ltr",
            }
        )

        # Avoid exposing Django's generic model-validator wording in Arabic UI.
        self.fields["username"].help_text = (
            "حتى 150 حرفًا. استخدم أحرفًا وأرقامًا والرموز @ . + - _ فقط."
            if ar
            else "Up to 150 characters. Use letters, digits and @ . + - _ only."
        )
        self.fields["phone_local"].help_text = (
            "يمكن إدخال الرقم بصيغة دولية مثل +971501234567 أو رقم محلي حسب الدولة المختارة."
            if ar
            else "Enter an international number such as +971501234567, or a local number for the selected country."
        )
        self.fields["password1"].help_text = (
            "استخدم كلمة مرور قوية وغير مستخدمة في حساب آخر."
            if ar
            else "Use a strong password that is not reused on another account."
        )
        self.fields["password2"].help_text = (
            "أعد إدخال كلمة المرور نفسها للتأكيد."
            if ar
            else "Enter the same password again for verification."
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "هذا البريد الإلكتروني مستخدم بالفعل."
                if get_language() != "en"
                else "An account with this email already exists."
            )
        return email

    def clean(self):
        cleaned = super().clean()
        country = cleaned.get("country")
        phone = cleaned.get("phone_local")

        if country and phone:
            try:
                cleaned["phone_e164_normalized"] = normalize_phone(country, phone)
            except ValueError:
                self.add_error(
                    "phone_local",
                    (
                        "رقم الهاتف غير صالح أو لا يطابق الدولة المختارة."
                        if get_language() != "en"
                        else "The phone number is invalid or does not match the selected country."
                    ),
                )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.SUPERVISOR
        user.email = self.cleaned_data["email"].lower().strip()
        user.country = self.cleaned_data["country"]
        user.phone_e164 = self.cleaned_data["phone_e164_normalized"]
        if commit:
            user.save()
        return user

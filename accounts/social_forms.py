from allauth.socialaccount.forms import SignupForm
from django import forms
from django.utils.translation import get_language

from core.countries import country_choices, normalize_phone

from .models import User


class GoogleSocialSignupForm(SignupForm):
    country = forms.ChoiceField()
    phone_local = forms.CharField(max_length=24, required=True)
    policy_acceptance = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ar = get_language() != "en"

        if "email" in self.fields:
            self.fields["email"].disabled = True
            self.fields["email"].help_text = (
                "تم التحقق من هذا البريد بواسطة Google."
                if ar
                else "This email was verified by Google."
            )

        self.fields["country"].choices = country_choices("ar" if ar else "en")
        self.fields["country"].initial = "AE"
        self.fields["country"].label = (
            "الدولة وكود الاتصال" if ar else "Country & calling code"
        )
        self.fields["phone_local"].label = "رقم الهاتف" if ar else "Mobile number"
        self.fields["policy_acceptance"].label = (
            "أوافق على الشروط والأحكام وسياسة الخصوصية"
            if ar
            else "I agree to the Terms & Conditions and Privacy Policy"
        )

        self.fields["country"].widget.attrs.update(
            {
                "class": "form-control",
                "data-country-select": "1",
            }
        )
        self.fields["phone_local"].widget.attrs.update(
            {
                "class": "form-control",
                "autocomplete": "tel",
                "inputmode": "tel",
                "data-phone-input": "1",
            }
        )

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
                    "رقم الهاتف لا يطابق الدولة المختارة."
                    if get_language() != "en"
                    else "The phone number does not match the selected country.",
                )
        return cleaned

    def save(self, request):
        user = super().save(request)
        user.role = User.Role.CUSTOMER
        user.country = self.cleaned_data["country"]
        user.phone_e164 = self.cleaned_data["phone_e164_normalized"]
        user.save(update_fields=["role", "country", "phone_e164"])
        return user

import phonenumbers
from django.utils.translation import override
from django_countries import countries


def dial_code(country_code):
    """Return the international calling prefix for an ISO-3166 alpha-2 region."""
    region = (country_code or "").strip().upper()
    if len(region) != 2:
        return ""
    code = phonenumbers.country_code_for_region(region)
    return f"+{code}" if code else ""


def address_country_choices(language="ar"):
    """All ISO countries, localized by django-countries, without phone prefixes."""
    lang = "en" if language == "en" else "ar"
    with override(lang):
        return [(code, str(name)) for code, name in countries]


def country_choices(language="ar"):
    """All ISO countries, localized and accompanied by their calling prefix."""
    lang = "en" if language == "en" else "ar"
    with override(lang):
        items = []
        for code, name in countries:
            dial = dial_code(code)
            label = f"{name} ({dial})" if dial else str(name)
            items.append((code, label))
        return items


def normalize_phone(country_code, value):
    """
    Parse and normalize a mobile/contact number into E.164.

    Security/quality rules:
    - The selected ISO country must be valid.
    - The phone's calling code must match the selected country calling code.
    - The number must be possible and valid according to libphonenumber metadata.
    """
    region = (country_code or "").strip().upper()
    raw = (value or "").strip()
    if not raw:
        raise ValueError("Phone number is required.")

    expected_country_code = phonenumbers.country_code_for_region(region)
    if not expected_country_code:
        raise ValueError("Unsupported country.")

    try:
        parsed = phonenumbers.parse(raw, None if raw.startswith("+") else region)
    except phonenumbers.NumberParseException as exc:
        raise ValueError("Invalid phone number.") from exc

    if parsed.country_code != expected_country_code:
        raise ValueError("Phone number does not match the selected country.")

    if not phonenumbers.is_possible_number(parsed) or not phonenumbers.is_valid_number(
        parsed
    ):
        raise ValueError("Invalid phone number.")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

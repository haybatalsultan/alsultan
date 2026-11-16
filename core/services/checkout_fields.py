"""Safe owner-controlled checkout field configuration.

Only fields that are already optional at the persistence layer may be changed.
System-critical checkout fields remain mandatory and cannot be hidden or relaxed.
"""

CONFIGURABLE_CHECKOUT_FIELDS = (
    "customer_email",
    "emirate",
    "city",
    "street",
    "building",
    "apartment_or_villa",
    "postal_code",
    "additional_notes",
)

SYSTEM_REQUIRED_CHECKOUT_FIELDS = (
    "customer_name",
    "customer_phone",
    "country",
    "area",
    "policy_acceptance",
)

DEFAULT_CHECKOUT_FIELD_CONFIG = {
    name: {"required": False, "visible": True}
    for name in CONFIGURABLE_CHECKOUT_FIELDS
}


def default_checkout_field_config():
    """Return a fresh JSON-serialisable default configuration."""
    return {
        name: values.copy() for name, values in DEFAULT_CHECKOUT_FIELD_CONFIG.items()
    }


def sanitise_checkout_field_config(value):
    """Whitelist supported fields and boolean options only."""
    raw = value if isinstance(value, dict) else {}
    cleaned = default_checkout_field_config()
    for name in CONFIGURABLE_CHECKOUT_FIELDS:
        candidate = raw.get(name)
        if not isinstance(candidate, dict):
            continue
        visible = candidate.get("visible")
        required = candidate.get("required")
        if isinstance(visible, bool):
            cleaned[name]["visible"] = visible
        if isinstance(required, bool):
            cleaned[name]["required"] = required
        # A hidden field can never be required.
        if not cleaned[name]["visible"]:
            cleaned[name]["required"] = False
    return cleaned

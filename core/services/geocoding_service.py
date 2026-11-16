from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings


class GeocodingUnavailable(Exception):
    pass


def _bounded_decimal(value, low, high):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Invalid coordinate.") from exc
    if number < Decimal(str(low)) or number > Decimal(str(high)):
        raise ValueError("Coordinate out of range.")
    return number.quantize(Decimal("0.000001"))


def reverse_geocode(latitude, longitude, *, language="ar"):
    lat = _bounded_decimal(latitude, -90, 90)
    lng = _bounded_decimal(longitude, -180, 180)
    key = settings.GOOGLE_MAPS_GEOCODING_API_KEY
    if not key:
        raise GeocodingUnavailable("Geocoding service is not configured.")

    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={
            "latlng": f"{lat},{lng}",
            "key": key,
            "language": "en" if language == "en" else "ar",
        },
        timeout=6,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") not in {"OK", "ZERO_RESULTS"}:
        raise GeocodingUnavailable("Geocoding provider rejected the request.")
    results = payload.get("results") or []
    if not results:
        return {
            "latitude": str(lat),
            "longitude": str(lng),
            "formatted_address": "",
        }

    components = {}
    for component in results[0].get("address_components", []):
        for kind in component.get("types", []):
            components.setdefault(kind, component)

    def long_name(*types):
        for kind in types:
            if kind in components:
                return components[kind].get("long_name", "")
        return ""

    def short_name(*types):
        for kind in types:
            if kind in components:
                return components[kind].get("short_name", "")
        return ""

    return {
        "latitude": str(lat),
        "longitude": str(lng),
        "country": short_name("country").upper(),
        "emirate": long_name("administrative_area_level_1"),
        "city": long_name("locality", "administrative_area_level_2", "postal_town"),
        "area": long_name("sublocality_level_1", "sublocality", "neighborhood"),
        "street": " ".join(
            part
            for part in (
                long_name("route"),
                long_name("street_number"),
            )
            if part
        ).strip(),
        "postal_code": long_name("postal_code"),
        "formatted_address": results[0].get("formatted_address", ""),
    }

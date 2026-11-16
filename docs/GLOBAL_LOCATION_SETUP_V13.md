# Global Current Location — HaybatAlsultan v13

## Browser key

Use a Google Maps browser key:

GOOGLE_MAPS_API_KEY=

Google Cloud restrictions:
- Application restriction: Websites / HTTP referrers
- Allow only development and production hosts you actually use
- API restriction: Maps JavaScript API + Geocoding API

`Places API (New)` is not required by v13. Enable it only when address autocomplete/search is added.

The browser key is intentionally visible to the browser. Its protection is Google Cloud HTTP-referrer + API restrictions. Never reuse this browser key as a server credential.

## Optional server fallback

GOOGLE_MAPS_GEOCODING_API_KEY=

This is optional and is only used by the existing server-side reverse-geocoding endpoint if the browser path cannot be used. If configured, use a separate server credential. Do not put a Websites/HTTP-referrer restricted browser key in this variable.

## Privacy behavior

- Geolocation is requested only after the customer presses "Use My Current Location".
- Coordinates are placed in the current form only.
- Nothing is persisted until the customer explicitly saves the address or submits the order.
- The customer can review and edit every generated address field.
- Manual address entry remains available if permission is denied or Google is unavailable.
- Production geolocation requires HTTPS.

## Global address behavior

Reverse geocoding attempts to fill:
- ISO country
- region/state/emirate
- city/locality
- district/neighborhood
- street
- postal code

Google does not guarantee every component for every location, so all visible address fields remain editable.

## Global countries and phone validation

v13 uses:
- django-countries 8.2.0 for the ISO country list and translated names
- phonenumbers 9.0.37 for international calling codes and E.164 validation

No database migration is required for the country expansion because stored country values remain ISO alpha-2 codes.

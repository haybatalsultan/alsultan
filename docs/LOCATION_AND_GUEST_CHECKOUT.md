# Guest Checkout, Country Codes and Location

## What changed

- Customer registration now asks for country and displays the matching international calling code.
- Phone numbers are normalized server-side to E.164.
- Checkout explicitly supports guest purchases; no account is required.
- Signed-in customers can reuse saved addresses.
- Customers can save multiple addresses and mark one default.
- Address fields now include country, emirate/region, city, area/district, street, building, apartment/villa, postal code and optional coordinates.
- "Use My Current Location" requests browser geolocation only after a customer presses the button.
- Reverse geocoding is performed server-side so the Google Geocoding API key is not exposed to browser JavaScript.

## Required production environment variable

GOOGLE_MAPS_GEOCODING_API_KEY=

Enable the Google Maps Geocoding API for that key before using automatic address filling.

If the key is not configured, the browser can still capture latitude/longitude after consent, but the customer must complete the human-readable address manually.

## Security

- Location lookup is POST-only and protected by Django CSRF middleware.
- Location lookup is rate-limited.
- Latitude and longitude are bounded and normalized before calling the provider.
- The geocoding API key remains server-side.
- `Permissions-Policy: geolocation=(self)` is emitted.
- Guest order confirmation is bound to the browser session.
- General order tracking still requires both order reference and the same normalized phone number.
- Only one default saved address is permitted per account at database level.

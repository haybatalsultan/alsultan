# v20.15 — Final Checkout Reservation Strategy

- Default inventory hold changed from 15 to 10 minutes.
- Cart remains non-reserving (anti-hoarding).
- Inventory hold starts once when the final checkout submission creates the order/payment step.
- Reservation expiry is immutable across refresh, WhatsApp/manual selection, Back, and payment-method changes.
- Stripe provider expiry remains separate (30+ minutes) on `PaymentAttempt`.
- At local inventory expiry, open Stripe Checkout Sessions are expired at Stripe before local inventory is released.
- Provider uncertainty fails closed: inventory remains held and cleanup retries later.
- Added tests for Stripe-expire-before-release, provider outage fail-closed behavior, and already-paid race protection.
- No database schema migration in this release.

# v20.15 — 10-Minute Payment-Step Reservation Strategy

## Final reservation policy

- Add to Cart does not reserve inventory.
- The final checkout submission creates the order and enters the payment step; the inventory hold starts exactly once at that boundary.
- Default inventory reservation TTL is 10 minutes (`RESERVATION_MINUTES=10`).
- Refresh, Back, WhatsApp/manual selection, and payment-method changes never rewrite `Reservation.expires_at`.
- Stripe Checkout keeps its provider-required expiry (`STRIPE_CHECKOUT_MINUTES`, minimum 30 minutes) in `PaymentAttempt.expires_at`; this never extends inventory reservation.
- When the local 10-minute inventory hold expires, an open Stripe Checkout Session is expired at Stripe **before** inventory is released.
- If Stripe is unreachable, a session is processing, or Stripe reports the payment complete/paid, inventory remains reserved. This fail-closed behavior prevents an oversell/payment race.
- Abandoned orders are retried by `python manage.py release_expired_reservations`.
- Reservation limits and temporary admin overrides remain unchanged.

## Production requirement

Schedule `release_expired_reservations` frequently (recommended: once per minute) so closed-browser sessions are reconciled without relying on a customer page reload.

# v20.13 Anti-Hoarding Reservation Security

- Add-to-cart no longer reserves inventory.
- Real reservation begins atomically at checkout.
- Default checkout reservation limit: 3 units.
- Owner may grant a registered customer up to 10 units for 15 minutes.
- Checkout endpoint remains protected by existing rate limiting.
- Refreshing cart/checkout does not extend an existing order reservation.
- Stripe paid converts reservation to sale using existing idempotent inventory logic.
- Expired order reservations release inventory using existing cleanup command.
- Overrides are server-side, account-bound, time-bound, owner+MFA only, and audited.

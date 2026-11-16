# Changelog v20.14

- Added `CheckoutReservationGuard` and migration `0016_checkoutreservationguard`.
- Added account/guest cross-session active reservation quota enforcement.
- Added sold-item cart invalidation after committed sale.
- Added server-side stale cart sanitization.
- Added live cart-count reconciliation for already-open cart pages.
- Added regression tests for Ahmed/Saeed same-piece purchase, stale checkout rejection, cross-session hoarding, and sold cart cleanup.

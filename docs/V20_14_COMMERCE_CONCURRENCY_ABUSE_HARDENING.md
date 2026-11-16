# v20.14 — Commerce Concurrency & Abuse Hardening

## Scope
Hardens Cart -> Checkout -> Reservation -> Payment -> Sale against stale carts, cross-session hoarding, concurrent purchase attempts and replay/stale browser states.

## Key rules
- Add-to-cart remains informational and does not reserve inventory.
- Checkout is the only place that starts an inventory reservation.
- Product rows are locked server-side before reservation.
- Active reservation quota is enforced across the authenticated account, not only the current cart.
- Guest quota is enforced across sessions using a one-way SHA-256 identity derived from the checkout phone.
- A SOLD product is invalidated from all remaining carts only after the sale transaction commits.
- Cart rendering removes permanently unavailable stale items; reserved-by-another-checkout items are not permanently deleted because they may become available after expiry.
- Checkout always revalidates stock under a row lock, so stale browser pages/POST requests cannot buy sold or fully-reserved stock.
- Cart pages perform a lightweight 20-second read-only status reconciliation and reload when the server-side cart count changed.

## Security notes
- Browser/JavaScript is never authoritative for inventory, limits or payment state.
- No raw SQL introduced.
- No payment secrets or Stripe identifiers exposed by cart reconciliation.
- Database-backed identity lock serializes reservation quota checks per customer principal.
- Existing Stripe webhook/reconciliation idempotency and inventory sale idempotency are unchanged.

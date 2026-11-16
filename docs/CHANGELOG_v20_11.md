# v20.11 — Scalable Customer Orders UI

## Customer order history
- Replaced the fixed 100-order load with server-side pagination (10 orders/page).
- Added authenticated-user-scoped search by order reference, item reference/SKU, and product snapshot name.
- Added allow-listed scope/status filtering and Active / Completed / All summary counts.
- Added distinct payment and fulfillment badges; Paid and Confirmed are no longer presented as action buttons.

## Order detail
- Added a compact visual fulfillment timeline: Paid → Confirmed → Preparing → Ready → Shipped → Out for delivery → Delivered.
- Kept payment status separate from order/fulfillment status.
- Shows the first 8 items and collapses additional items under an explicit disclosure control.
- Preserved secure tracking link handling and all existing Stripe/manual-payment behavior.

## Security
- All history/detail queries are scoped to `request.user` server-side.
- Public IDs do not bypass ownership checks.
- Filter/status inputs are allow-listed; search length is bounded.
- No new models, migrations, payment logic, inventory logic, or notification logic.

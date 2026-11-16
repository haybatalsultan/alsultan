# v19.6 — Cart Recovery, Order Proof & Timeline

## Added
- Cart item snapshots for customer recovery UX. These are informational only.
- Checkout always recalculates price, promotion and availability from locked server-side product rows.
- Immutable OrderItem purchase snapshot: product reference, SKU, names, price/discount/promotion/gift, image, category and verification state.
- Customer `My Orders` page scoped strictly to `request.user`.
- Existing order detail remains owner-scoped and returns 404 for another customer's UUID.
- Guest order verification continues to require both order reference and the checkout phone number.
- Order tracking POST is already protected by the hardened rate-limit middleware.
- Business order timeline for creation, payment and status transitions.
- Owner/supervisor timeline visibility is controlled by `view_order_timeline`.
- Incomplete-cart visibility is controlled independently by `view_abandoned_carts`.
- Master-data access discovered during privilege review is now explicitly controlled by `manage_master_data`.
- Order workflow transitions are explicit; `view_orders` alone can no longer mark an order delivered.
- Timeline records block normal and bulk ORM update/delete operations.

## Privacy
- Public/guest tracking never exposes delivery address, coordinates, email, audit IPs, or management actor details.
- Detailed management timeline is shown only with explicit permission.
- Ordinary browsing/clickstream is not tracked.

## Verification
Static checks available in this build environment passed. The full Django suite must be run in the project's own virtual environment because Django is not installed in the artifact runtime.

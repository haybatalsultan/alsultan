# v20.9.8 — Management Workflow & Security TEST

Built from v20.9.7 Inventory & Delivery TEST. v20.9.7 remains the rollback reference until this release passes local tests.

## Fixed
- Owner order page now renders the persisted `Order.status` and `Order.payment_status`; it no longer defaults visually to Pending/Unpaid.
- Stripe payment state is read-only in management and cannot be manually forged through the legacy generic payment action.
- Manual/WhatsApp payment has an explicit persisted payment method and secure manual confirmation workflow.
- Manual confirmation records actor/time, confirms the order, and consumes reservations exactly once.
- Paid orders cannot be cancelled through the ordinary cancellation route.
- Unpaid cancellation now releases reservations atomically.
- Fulfilment and delivery changes are blocked until payment is confirmed.
- Shipping fields are localized and tracking URLs require HTTPS.

## Dashboard
- Replaced misleading low-stock-only overview with operational metrics:
  - total orders
  - awaiting payment
  - paid & confirmed
  - preparing
  - ready for delivery
  - out for delivery
  - delivered
  - products available for sale
  - sold out
  - low stock based on free quantity (`available - reserved`)
  - paid revenue / today revenue (Owner)
- Added Delivery & Shipping shortcut.
- Recent orders now show both order and payment state.
- Orders list shows payment method and supports a delivery queue filter.

## Payment method persistence
Migration `orders.0011_payment_method_and_manual_confirmation` adds:
- `payment_method`: UNSET / STRIPE / MANUAL
- `manual_paid_at`
- `manual_paid_by`

Existing orders that already have a `PaymentAttempt` are backfilled as Stripe.

## Required validation
```powershell
python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 2
```

# Haybat Al Sultan — v20.9.8 Management Workflow Security Review

Scope: management dashboard, order management, Stripe/manual payment separation, inventory conversion/release, delivery workflow, customer manual-payment selection.

## Controls reviewed / enforced

- Management routes remain protected by authenticated Owner/Supervisor role + mandatory MFA middleware/decorator checks.
- Order management mutations remain CSRF-protected POST operations.
- Customer manual-payment selection is POST-only and still uses the existing order-access check (authenticated owner of order or recent guest-order session marker).
- Stripe payment state is read-only in the Management Portal. A generic payment-status selector is no longer exposed and the legacy mutation action is denied.
- Stripe verification continues to use signed webhooks and server-to-server reconciliation; no browser-supplied amount/status is trusted.
- Manual payment confirmation requires `mark_paid`; Stripe-associated orders and active/paid Stripe attempts cannot be marked paid manually.
- Manual confirmation uses a database transaction and row locks, converts active reservations to Sale exactly once, records actor/time, and is idempotent on replay.
- Paid orders cannot be cancelled through the ordinary cancellation path. They require the future refund/return workflow.
- Unpaid cancellation releases active reservations atomically so stock cannot remain stranded.
- Fulfilment transitions are server-validated. Unpaid orders cannot move into Preparing/Ready/Shipped/Out-for-delivery/Delivered.
- Shipping details require `ship_orders`, a paid active order, explicit field validation, and HTTPS for tracking URLs.
- Templates use Django auto-escaping; no `mark_safe`/unsafe HTML was introduced.
- Audit entries record payment source/status transitions and management actor without card data, API keys, webhook signatures, or secrets.
- Dashboard values are calculated server-side from persisted order/inventory state. Free inventory uses `available_quantity - reserved_quantity` rather than the old low-stock shortcut.
- Stripe/manual payment method is explicitly persisted on the Order. Existing orders with a PaymentAttempt are backfilled as Stripe by migration `0011`.

## Regression tests added

`tests/test_management_payment_workflow_v20_9_8.py` covers:

- Management page rendering persisted Paid/Confirmed values rather than form defaults.
- Stripe payment status not exposed as an editable management selector.
- Manual payment confirmation permission enforcement.
- Manual confirmation consumes inventory once and survives replay without a second deduction.
- Active Stripe attempt blocks manual payment confirmation.
- Unpaid orders cannot enter fulfilment or edit shipping details.
- Customer manual-payment selection is POST-only and records the method.
- Dashboard separates available and sold-out inventory.
- Unpaid cancellation releases reservations.
- Paid cancellation is blocked until a refund/return workflow exists.

Existing Stripe reconciliation/webhook tests were extended to assert that verified Stripe payment also records `payment_method=STRIPE`.

## Local validation required before approval

Run in the project virtual environment:

```powershell
python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 2
```

Before Render production also run:

```powershell
python manage.py check --deploy --settings=config.settings.production
```

Production payment testing must remain in Stripe Sandbox until staging passes. Never commit `.env`, `sk_*`, `whsec_*`, database dumps, or customer payment material.

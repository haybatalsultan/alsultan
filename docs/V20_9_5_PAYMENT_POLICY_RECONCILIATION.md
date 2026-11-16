# v20.9.5 — Payment Policy + Stripe Reconciliation

## Owner payment policy
The existing `StoreSetting.online_payment_enabled` and `StoreSetting.whatsapp_checkout_enabled` fields are now used as the owner-controlled payment policy. No schema migration was added.

Available combinations:
- Stripe only
- Manual WhatsApp payment follow-up only
- Both methods

At least one method must remain enabled. Online payment cannot be enabled unless Stripe is configured in the environment.

Disabling online checkout stops new Stripe sessions, but does not disable webhook processing or reconciliation for already-started payments.

## Stripe reconciliation
Stripe webhook remains the primary payment confirmation mechanism.

The success page now performs a server-to-server fallback reconciliation for an existing recorded PaymentAttempt. It retrieves the recorded Checkout Session directly from Stripe and validates:
- Checkout Session ID against the local PaymentAttempt
- order public ID metadata
- order reference metadata
- currency
- total amount
- remote Stripe session status
- remote Stripe payment status

Only a remote `complete + paid` session can mark the order paid and confirm it.

## Operations fallback
`python manage.py reconcile_stripe_payments`

Optional:
- `--order HS-...`
- `--limit 100`

The command never prints Stripe payloads or secrets.

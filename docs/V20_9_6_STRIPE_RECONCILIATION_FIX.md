# v20.9.6 Stripe Reconciliation Fix

- Reconciliation no longer converts the whole Stripe SDK object.
- Only the allow-listed Checkout Session fields needed for verification are read.
- Server-to-server retrieval uses `stripe.checkout.Session.retrieve`, matching the sandbox path verified manually.
- Existing validation remains mandatory: Checkout Session ID, order metadata, amount, currency, payment status and session status.
- Payment state transitions remain idempotent and reuse the same `_mark_paid` path.
- No model or migration changes.
- No API keys, webhook secrets, or provider payloads are logged or stored in source.

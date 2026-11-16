# v20.9.3 Stripe Webhook Diagnostic TEST

Purpose: expose the traceback for unexpected Stripe webhook processing errors without logging Stripe payloads, signatures, API keys, or webhook secrets.

No payment workflow, model, migration, reservation, or reconciliation logic changed.

After starting Django and the Stripe CLI listener, trigger `checkout.session.completed`. Inspect the Django terminal for `stripe_webhook_processing_failed` and the traceback immediately below it. Do not share secrets or the webhook signing secret.

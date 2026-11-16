# Haybat Alsultan v20.9 — Stripe Sandbox Integration

## Scope
- Stripe Checkout hosted payment page.
- One Haybat order reference for the checkout; each OrderItem keeps its own HS item reference/SKU snapshot.
- Server-side amount/currency calculation only.
- Signed Stripe webhook reconciliation.
- Webhook idempotency through `StripeWebhookEvent.event_id`.
- Local payment attempt tracking without storing card data.
- Reservation extension while Checkout is open; release on expired/failed session.
- Successful verified payment sets `payment_status=PAID` and confirms a pending order.
- Refund webhook updates only financial payment status; fulfillment state is not silently rewritten.

## Required local `.env`
Never commit or share these values:

```env
STRIPE_ENABLED=True
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_CURRENCY=aed
STRIPE_CHECKOUT_MINUTES=30
```

Local development refuses `pk_live_` / `sk_live_` credentials.

## Local setup

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py test -v 2
python manage.py runserver
```

In a second PowerShell terminal:

```powershell
stripe listen --forward-to http://127.0.0.1:8000/orders/payment/stripe/webhook/
```

Copy the `whsec_...` value printed by `stripe listen` into `STRIPE_WEBHOOK_SECRET` in `.env`, restart Django, and keep the listener running.

## Sandbox test flow
1. Add available products to cart.
2. Complete Haybat checkout.
3. The server creates one order and redirects to Stripe Checkout.
4. Pay with a Stripe test payment method.
5. Stripe CLI forwards the signed event to Django.
6. Django verifies signature + amount + currency + order metadata.
7. Payment becomes PAID and pending order becomes CONFIRMED only after verification.

Do not use live credentials until the complete sandbox test checklist passes.

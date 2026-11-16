# v20.10 Notifications & Smart Tracking Menu

- Customer account menu shows `Track My Order` only when an authenticated customer has an active order.
- Active-order lookup is server-side and scoped to `request.user`; no public ID from the browser is trusted for ownership.
- Public `/orders/track/` continues to require order reference + matching phone and keeps its existing rate limit.
- Administration email defaults to the configured store email and can be changed only by OWNER.
- Email notifications use a persistent unique notification record to prevent duplicate sends from Stripe webhook retries/reconciliation.
- Email bodies do not contain card data, Stripe secret keys, webhook secrets, Checkout Session IDs, PaymentIntent IDs, or internal management notes.
- Notification delivery is scheduled with `transaction.on_commit(..., robust=True)` so an SMTP failure cannot roll back an order, payment, inventory conversion, or delivery status transition.
- Email failures are logged only by event key and exception type; recipient and message body are not logged.
- Customer shipping emails are limited to SHIPPED / OUT_FOR_DELIVERY / DELIVERED.
- External tracking URLs remain subject to the existing HTTPS validation in shipping management.
- SMTP credentials remain environment-only.

# v20.14.1 Immutable Reservation Expiry

- Reservation.expires_at is created at checkout and is not modified by refresh, WhatsApp selection, payment-method switching, or Stripe session creation.
- Stripe provider windows are stored only on PaymentAttempt.expires_at.
- An active Stripe PaymentAttempt can protect a legitimate in-progress payment from automatic inventory release without rewriting the original reservation deadline.
- Only OWNER or a SUPERVISOR with `extend_reservations` can extend an active unpaid reservation.
- Allowed extension values are 15, 30, or 60 minutes.
- Expired reservations cannot be revived.
- Active Stripe sessions cannot be extended from management.
- Every authorized extension is written to the order timeline and audit log.

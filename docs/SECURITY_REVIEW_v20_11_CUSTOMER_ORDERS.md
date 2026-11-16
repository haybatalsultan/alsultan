# Security Review — v20.11 Customer Orders

- **IDOR:** order history begins from `Order.objects.filter(user=request.user)`; detail lookup includes `user=request.user`.
- **Search/filter manipulation:** free text is trimmed/bounded to 80 chars; status/scope values are allow-listed before ORM use.
- **SQL injection:** Django ORM `Q()` lookups only; no raw SQL.
- **XSS:** templates use Django auto-escaping; no `safe` rendering added.
- **External tracking URLs:** existing URL model validation and `rel="noopener noreferrer nofollow"` preserved.
- **Payment/inventory integrity:** no changes to Stripe, webhook, reconciliation, reservation, or inventory consumption services.
- **Performance:** pagination prevents unbounded customer order-history rendering; product details are collapsed after 8 rows.
- **Authorization:** all new controls are read-only customer presentation; no new mutation endpoints were added.

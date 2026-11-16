# Haybat Al Sultan v20.7.2 — Loyalty Tier Refinement

This update changes only the server-derived customer loyalty ladder:

- 0 qualifying delivered orders: Customer
- 1: New Customer
- 2–3: Silver Customer
- 4–6: Gold Customer
- 7–9: Platinum Customer
- 10+: Royal Customer

Security rules remain unchanged:
- Customer cannot submit or edit a loyalty tier.
- Only DELIVERED orders qualify.
- Fully refunded orders do not qualify.
- Returned orders do not qualify because their status is no longer DELIVERED.
- Tier is recalculated from server-side order records.

No migration is required for v20.7.2 because no loyalty tier is stored in the User model.

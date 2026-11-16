# Haybat Alsultan v20.8 — Ambassador Program Review

## Fixed business rules
- Earning: each complete AED 1,000 of eligible referred product spend earns exactly 25 integer points.
- Redemption: each complete 1,000 points equals AED 25.
- No fractional points or fractional redemption blocks.
- Each earned point batch expires 12 months from its own earning timestamp.
- Referral points become available only after the referred order is both PAID and DELIVERED.
- Cancelled, returned, fully refunded, or partially refunded referred orders revoke remaining unspent referral points conservatively.

## Security controls
- Ambassador codes are random, non-sequential `HSA-XXXXXXXX` values using an ambiguity-reduced alphabet.
- Authenticated self-referral is blocked by account identity; guest self-referral is also blocked against the ambassador account phone/email.
- One referral record per order is enforced by a database OneToOne relationship.
- Referral code validation, earning, redemption and balance checks are server-side.
- Discount redemption uses FIFO point batches and records per-batch allocations so cancelled/refunded orders can restore the exact consumed points to their original expiry batches.
- The Owner alone can enable/disable the program. Supervisors may view ambassador reporting only when they already have `view_customers` permission.
- Disabling the program does not delete codes, point history, referrals, or prior records.
- Point ledger entries provide a trace for earn, redeem, expire and reversal activity.
- Existing customer loyalty tiers remain independent from ambassador points.

## Privacy
- Customers do not see referred buyers' names, phone numbers, email addresses, or order references in their ambassador account.
- Management reporting exposes referral buyer/order data only behind the existing MFA-protected management portal and customer-view permission checks.

## Deployment
Run migrations before testing:

    python manage.py migrate

Then enable the feature from Owner → Management Portal → Haybat Alsultan Ambassadors.

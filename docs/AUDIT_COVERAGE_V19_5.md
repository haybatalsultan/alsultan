# Haybat Al Sultan — Audit Coverage v19.5

## Audit design

The Audit & Security Center is owner-only and read-only.

Two streams are intentionally separated:

1. **Business Audit Trail** — state-changing application/business operations.
2. **Security Events** — authentication, MFA, access denial and security controls.

Read-only page views and searches are **not** written to the business audit table. This is deliberate to avoid excessive logging, customer-privacy duplication, and storage noise. Web/access logs remain the appropriate source for ordinary GET traffic.

## Business operations covered

- Categories: create, edit, activate/deactivate
- Materials: create, edit, activate/deactivate
- Products: create, edit
- Product images: upload, metadata changes, primary-image change, delete
- Pricing: before/after changes
- Inventory: quantity before/after plus business reason
- Orders: creation, status changes
- Payments: payment-status changes
- Promotions: create, edit, activate/deactivate
- Supervisors: account creation
- Access control: complete permission before/after snapshot
- Customer addresses: creation event with privacy-minimized metadata
- Wishlist: add/remove
- Cart: item add/remove
- WhatsApp follow-up consent: enabled/disabled
- Checkout: order-created snapshot with total/currency/status/item count

## Security events covered

- Registration
- Login success/failure
- Logout
- Owner MFA enrollment requirement
- MFA challenge, success/failure
- MFA setup success/failure/cancel
- Denied management access
- Rate-limit behavior remains protected by the v17 hardening and can be correlated through application logs/request IDs

## Data recorded per business event

- Actor FK when available
- Actor username snapshot
- Actor role snapshot
- Action and category
- Success/failure outcome
- Source (Management / Storefront)
- Object type and stable reference
- Request ID
- HTTP method and path
- Validated network peer (`REMOTE_ADDR`)
- User-Agent
- Before values
- After values
- Privacy-minimized metadata
- HMAC integrity signature

## Sensitive-data policy

The audit service recursively redacts values whose keys indicate passwords, secrets, tokens, authorization data, cookies or session material.

It intentionally does not duplicate precise customer address coordinates or raw WhatsApp contact numbers into the audit trail.

## Integrity and immutability

- Model-level `save()` and `delete()` mutation is blocked for existing audit/security records.
- QuerySet `update()` and `delete()` are blocked through the application ORM.
- New audit records receive an HMAC-SHA256 integrity signature.
- Production requires a dedicated `AUDIT_LOG_SIGNING_KEY`.
- Render Blueprint generates the signing key as a secret environment value.
- Legacy audit rows created before v19.5 are shown as **Legacy unsigned record**, not as tampering failures.

This integrity signature protects against accidental/application-level record mutation and provides evidence of lower-level database tampering when the signing key remains secret. It is not a substitute for database access controls, backups, or external immutable log storage.

## Pre-Render verification

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test --settings=config.settings.test
python scripts/security_static_check.py
python manage.py collectstatic --noinput
```

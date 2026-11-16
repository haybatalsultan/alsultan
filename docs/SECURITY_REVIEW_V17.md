# HaybatAlsultan Store — Security Review v17

Date: 2026-08-15

## Scope reviewed

This review focused on the current Django application and the security-sensitive flows that exist in v16/v17:

- Login and local authentication
- Owner MFA and pre-authentication flow
- Password reset
- Google OAuth
- Rate limiting
- Request/audit network attribution
- Session and CSRF behavior
- Management authorization / object scoping
- Cart / checkout / order pricing
- Product image uploads and Cloudinary
- Production settings and Render deployment
- Shared cache behavior across Gunicorn workers
- Secret packaging and obvious dangerous-code patterns

This is a source-code and configuration review plus regression-test authoring.
It is not an external black-box penetration test and does not prove that no
unknown vulnerability exists.

## Fixed — HIGH: Forwarded-header rate-limit bypass

Previous behavior trusted:

- `CF-Connecting-IP`
- the first value of `X-Forwarded-For`

An attacker able to supply/alter these headers could rotate them between
requests and change the IP-derived cache key.

v17 changes:

- Rate limiting does not use `CF-Connecting-IP` or `X-Forwarded-For`.
- Login is limited by a keyed HMAC of the normalized username/account target.
- Password reset is limited by a keyed HMAC of the normalized email target.
- MFA is limited by the pre-authenticated/authenticated user flow.
- Guest checkout/tracking/follow-up use stable flow/customer identifiers.
- Existing session identifiers add a supplementary bucket when available.
- Raw usernames/emails/session IDs are never put in Redis cache keys.
- `REMOTE_ADDR` is optional only as a direct-network-peer bucket.
- That peer bucket is explicitly disabled in Render production because a
  Render edge/load-balancer address can be shared by many customers.

Regression tests rotate both forwarded headers between every login/reset
attempt and verify that the stable account/email limit still returns HTTP 429.

## Fixed — HIGH: Per-process rate limits on four Gunicorn workers

The Blueprint starts Gunicorn with four workers. A local-memory cache is
process-local, so security counters must not depend on it in production.

v17:

- Production refuses to boot without `REDIS_URL`.
- `render.yaml` provisions `haybat-security-cache` as Render Key Value.
- The web service receives its internal `connectionString` as `REDIS_URL`.
- All workers therefore use the same Redis/Valkey-compatible cache.
- Production rate limiting fails closed (HTTP 503) if the security cache is
  unavailable rather than silently disabling throttling.

The free Key Value instance uses persistence off. That is acceptable for
short-lived fixed-window rate-limit counters; persistent application state is
not stored there.

## Fixed — Audit network attribution

The previous `SecurityEvent.ip_address` and `AuditLog.ip_address` path could
store attacker-provided forwarded headers as though they were authoritative.

v17:

- The authoritative `ip_address` field stores only validated `REMOTE_ADDR`
  (the immediate network peer).
- Forwarded IP values are not stored as authoritative IPs.
- SecurityEvent may store only a keyed, shortened correlation hash of a
  syntactically valid X-Forwarded-For hint, explicitly marked
  `forwarded_ip_trusted=False`.
- CF-Connecting-IP is ignored by `client_ip()`.

Important trade-off: behind Render, the authoritative network peer can be a
Render proxy rather than the customer's true IP. That is intentional. The app
does not pretend an unverified forwarding header is trustworthy.

## Preserved — Microsoft 365 email fix

The validated development behavior is included:

- If `EMAIL_HOST` is configured, development uses Django SMTP backend.
- Otherwise development falls back to console email.
- `EMAIL_USE_SSL` is supported.
- TLS and SSL cannot both be enabled.
- `.env.example` contains non-secret Microsoft 365 settings for
  `info@haybatalsultan.com`; the mailbox password remains blank.

## Reviewed controls that remain in place

- Django admin is not mounted.
- CSRF middleware remains active; no runtime `csrf_exempt` found.
- Logout and destructive image/toggle/cart actions are POST-only where
  applicable.
- Owner management sessions require MFA verification.
- Management permission checks remain server-side.
- Product image IDs are scoped to their parent product.
- Order detail is scoped to the authenticated user.
- Guest confirmation is scoped by a recent-order session marker.
- Cart item deletion is scoped to the caller's cart.
- Checkout recalculates product prices server-side under a DB transaction;
  browser-supplied product prices are not trusted.
- Inventory is locked/reserved server-side during order creation.
- Uploads validate file size, decoded image format, pixel count, corruption,
  and decompression-bomb warnings before Cloudinary upload.
- Google OAuth auto-link by email remains disabled and social login remains
  customer-only.
- No real `.env`, SQLite database, virtual environment, Google key, OAuth
  secret, or Cloudinary secret is packaged in the artifact.
- Django is pinned to 6.0.8, which contains the Aug 4 2026 Django security
  fixes.

## Remaining security hardening items (not classified as a discovered
unauthenticated exploit in this review)

### Supervisor MFA — superseded by v19.6.2

This historical v17 recommendation has now been implemented. MFA is mandatory
for both OWNER and SUPERVISOR management accounts before Management Portal
access.

### TOTP secrets are stored in the application database

TOTP verification requires access to the shared secret. The current model
stores it in a normal database field. A full database compromise could
therefore weaken the second factor.

Recommendation: before handling high-value production administration,
consider application-level encryption using a dedicated rotation-capable key
that is separate from the database and preferably separate from Django
SECRET_KEY.

### Application throttling is not a WAF

The new rate limiter protects account-targeted brute-force attempts even when
forwarded headers rotate. It should still be combined with Render's edge
protections and monitoring for broad volumetric or distributed attacks.

### External penetration testing was not performed

No source-code review can honestly guarantee that the application has zero
vulnerabilities. Before launch, run the full Django tests in the project
environment and perform a production-like black-box test of authentication,
authorization/IDOR, checkout, uploads, OAuth, password reset, and security
headers.

## Required local verification

After replacing the project:

```powershell
pip install -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --settings=config.settings.test
python scripts/security_static_check.py
python manage.py collectstatic --noinput
```

Expected:
- no pending migrations
- all Django tests pass
- project security invariant scan passes

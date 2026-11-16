# Master Data, Language & Contact Update — Security Review

## Scope
- Owner/Supervisor Master Data hub for Categories and Materials.
- Pagination and search for both master-data lists.
- Server-generated immutable slugs.
- Archive/reactivate workflow instead of destructive deletion.
- Category image URL restricted to HTTPS Cloudinary delivery URLs.
- Arabic forced as the first-visit default while explicit user language choice persists.
- Globe language selector uses Django `set_language` with POST + CSRF and a local path as `next`.
- Official contact identity: `HaybatAlsultan`, `info@haybatalsultan.com`, and the configured store phone/WhatsApp.

## Authorization review
- Every master-data endpoint is behind `staff_required`.
- Customer access is denied server-side with 403.
- Owner access continues to require verified MFA on the current management session.
- Supervisors are intentionally allowed to create, edit, archive, and reactivate Categories and Materials.
- Pricing and cost fields remain isolated behind owner-only authorization and are not added to master-data forms.

## Data integrity review
- No hard-delete routes were introduced for Category or Material.
- Category/Material relations remain `PROTECT` on Product.
- New Product forms show active Category/Material records only; an existing Product can retain its archived current value while editing.
- Master-data slugs are generated server-side and become immutable after first save.
- Create/update/status changes are wrapped with their AuditLog write in a database transaction.

## Web security review
- All state-changing master-data actions use POST and CSRF protection.
- No `csrf_exempt`, raw SQL, `|safe`, `mark_safe`, `eval`, or `exec` was introduced.
- Language switching does not accept an arbitrary external redirect target from the template; `next` is `request.path` only.
- Category image URL input is limited to `https://res.cloudinary.com/`.

## Verification
- Python `compileall`: expected PASS in package verification.
- Static security-pattern scan: expected PASS in package verification.
- Automated test suite now contains 52 tests; run locally with Django installed before promotion to staging/production.

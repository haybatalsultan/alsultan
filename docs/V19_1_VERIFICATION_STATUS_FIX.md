# HaybatAlsultan Store v19.1

## Product verification
The previous multi-field certificate model has been replaced by one owner-controlled field:

- NONE — no verification badge
- INSPECTED — product inspected
- CERTIFIED — certified product

The storefront displays only the selected status. Supervisors cannot change this trust claim.

## Database migration
Migration `0009_product_verification_status.py`:
1. Adds `verification_status`.
2. Preserves existing `has_certificate=True` records as `CERTIFIED`.
3. Removes the faulty certificate constraint and old certificate metadata fields.
4. Adds a database constraint allowing only NONE / INSPECTED / CERTIFIED.

## Security
- Verification status is owner-only in management forms.
- A forged supervisor POST field is ignored server-side.
- Invalid raw database values are rejected by a database constraint.
- No certificate URL or document upload is exposed in this version.
- v17 rate-limiting and proxy-spoofing protections remain unchanged.

## Required local verification
```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test --settings=config.settings.test
python scripts/security_static_check.py
python manage.py collectstatic --noinput
```

Do not deploy to Render until the Django suite returns `OK`.

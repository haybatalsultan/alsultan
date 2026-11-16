# Haybat Al Sultan v19.6.2 — Mandatory Supervisor MFA

MFA is now mandatory for every management account:

- OWNER
- SUPERVISOR

A supervisor with correct username/password but without an enabled TOTP device
is not authenticated into the Management Portal. The user is first sent to the
local MFA enrollment flow. Once enrolled, every new login requires a TOTP code.

Defense in depth is enforced both by management middleware and the
`staff_required` decorator so an old authenticated session cannot bypass MFA.

Customers are not forced to enroll MFA by this policy.

## Required local verification

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test --settings=config.settings.test
python scripts/security_static_check.py
python manage.py collectstatic --noinput
```

Expected test count for this package: 167.

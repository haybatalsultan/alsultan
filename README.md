# Haybat Alsultan Store — Clean Release Candidate v20.19

Production-oriented Django storefront for Haybat Alsultan.

## Current stable baseline

- Checkout field settings controlled from the Owner portal.
- Checkout idempotency protection preserved.
- Stripe Checkout enabled according to Owner payment settings.
- WhatsApp manual-payment redirect supported by the CSP allowlist.
- Mobile-first cart motion with reduced-motion accessibility support.
- Django Admin is not intended for normal production administration; use the custom Management Portal.

## Local verification

```powershell
python manage.py makemigrations --check
python manage.py check
python manage.py test
```

## Security verification

```powershell
pip check
pip-audit
bandit -r . -x .venv,venv,migrations,tests
semgrep scan --config auto --error --exclude .venv --exclude venv --exclude media --exclude staticfiles --exclude node_modules --exclude security-reports --exclude .ruff_cache --exclude .pytest_cache --exclude .mypy_cache .
ruff check .
```

## Production build

Render rebuilds collected static assets during deployment using:

```text
python manage.py collectstatic --noinput
```

Do not commit `.env`, local databases, generated `staticfiles/`, media uploads, caches, logs, virtual environments, or security reports.

# Haybat Al Sultan v20.7 — Loyalty, Smart Accountant & Risk Signals

## Loyalty
- 0 qualifying delivered orders: Customer
- 1: New Customer
- 2–3: Silver Customer
- 4–6: Gold Customer
- 7–9: Platinum Customer
- 10+: Royal Customer
- Returned and fully refunded orders do not qualify.
- Tier is derived from server-side orders; there is no writable tier field.

## Smart Accountant
Owner-only. Uses a dedicated delivery timestamp and immutable historical cost
snapshots for new orders. Legacy data without trustworthy historical snapshots
is explicitly excluded from fabricated profit calculations.

Displayed profit is gross product profit before operating expenses that are not
tracked by the application.

## Risk signals
Advisory review signals only (cancellations, returns, failed payments, high
order activity). No automatic blocking, accusation, or tier change.

## Required local verification
```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate
python manage.py test --settings=config.settings.test
python scripts/security_static_check.py
python manage.py collectstatic --noinput
```

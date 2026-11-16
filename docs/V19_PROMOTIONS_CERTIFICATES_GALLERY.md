# HaybatAlsultan Store v19

## Included
- RTL featured-category ordering: Misbah appears at the far right in Arabic.
- Flexible Cloudinary product gallery: upload any number up to the configured maximum; choose primary image and order.
- Owner-only product certificate status and metadata.
- Owner-only promotions/discounts/gifts page.
- Promotion scopes: all products, selected products, selected categories.
- Discount types: percentage, fixed amount, gift only.
- Start/end dates, priority, active/inactive state.
- Secure server-side checkout recalculation and non-stacking pricing.
- Order snapshots for base price, discount, promotion label and gift label.

## Security
Promotion and certificate actions do not trust browser-side prices. Checkout locks products and recalculates the active offer server-side. Promotion management is owner-only and uses existing owner MFA/session enforcement. Activation is POST-only. Database constraints protect core business rules.

## Local verification
Run:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test --settings=config.settings.test
python scripts/security_static_check.py
python manage.py collectstatic --noinput
```

Do not deploy to Render until the full Django suite returns `OK`.

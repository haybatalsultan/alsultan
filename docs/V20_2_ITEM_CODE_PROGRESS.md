# Haybat Al Sultan v20.2 — Item Code Progress

The management UI now displays the **last persisted** HS item code on the
Create Product page and Products Management page.

It intentionally does not display a promised "next number." The next SKU is
created only after the database assigns the product primary key, preserving the
existing concurrency-safe allocation.

After a successful product create, the actual generated code is shown in the
success message.

No migration is required for this UI-only update.

## Local verification

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --settings=config.settings.test
python scripts/security_static_check.py
python manage.py collectstatic --noinput
```

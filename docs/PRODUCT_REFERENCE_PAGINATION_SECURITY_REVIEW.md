# Product Reference, Search & Pagination Security Review

## Scope

This review covers the permanent product reference, management search, numbered pagination, product create/edit workflow, pricing separation, order-item snapshot integration, and management list queries.

## Security decisions

- Product references are generated server-side and are never accepted from management forms.
- The database enforces uniqueness for `Product.product_reference`.
- Application code rejects attempts to mutate an existing product reference.
- Product references are separate from internal UUIDs and SKUs; UUIDs remain the identifier used by sensitive management routes.
- Owner-only pricing remains in `PricingForm` and is not included in the operational product form.
- Injecting `cost_price`, `selling_price`, or `discount_price` into a supervisor product-edit POST does not bind those fields.
- Management search uses Django ORM `Q` objects only; no user input is interpolated into SQL.
- Search input is length-limited before ORM filtering.
- Global management search returns only entity classes the current staff account is authorized to view.
- Pagination is server-side and preserves escaped query parameters; arbitrary page values are handled through Django `Paginator.get_page()`.
- Order item snapshots now preserve the permanent human-readable product reference instead of depending only on the current product row.
- Existing historical order-item UUID references are migrated safely, including rows whose product has been removed.
- Audit entries prefer the product reference/order reference for support-friendly traceability without exposing cost data.

## Verification performed in build environment

- Python `compileall`: PASS
- Static security pattern scan: PASS
- No `csrf_exempt`, raw SQL, `mark_safe`, template `|safe`, `eval`, or `exec` introduced.
- No owner cost price added to storefront templates or management search results.

## Required local verification

Run after extracting the update and keeping your existing `.env`:

```powershell
python manage.py migrate
python manage.py check
python manage.py test --settings=config.settings.test
```

A real PostgreSQL staging run remains required before Production, especially for migrations and concurrency behavior.

# Haybat Al Sultan Management Portal — Review

## UI/UX pass
- Replaced heavy black statistic cards with lightweight ivory/white cards and restrained gold accents.
- Added authenticated greeting using the server-side Django user session.
- Added role and username display.
- Added explicit POST-only sign-out form with CSRF token.
- Reworked management links into responsive tool cards.
- Owner-only tools are not rendered for supervisors. This is UX hardening only; server-side authorization remains mandatory.
- Reworked recent orders into a compact responsive table and a dedicated empty state.

## Security second pass
- Pricing remains OWNER-only through `require_owner()` and is not exposed in the dashboard context for supervisors.
- Supervisor tool visibility is derived from server-side permission checks (`can()`), not browser state.
- Owner-only supervisor and audit endpoints continue to call `require_owner()` server-side.
- Logout remains `POST`-only and uses Django CSRF protection.
- Dashboard values come from ORM queries; no raw SQL or user-built SQL was introduced.
- User-controlled text remains Django auto-escaped; no `|safe` or `mark_safe` was added.
- Public database IDs are not introduced into management links; existing UUID public IDs remain in use.
- No new secrets, credentials, tokens, or inline privileged data were added to templates.

## Verification required on developer machine
Run:

```powershell
python manage.py check
python manage.py test --settings=config.settings.test
python scripts/security_static_check.py
```

A production release should also be tested with PostgreSQL and `check --deploy` using production-like environment variables.

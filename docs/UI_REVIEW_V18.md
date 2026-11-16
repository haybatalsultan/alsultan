# HaybatAlsultan UI Consistency Review — v18

## Fixed
- Added branded django-allauth Google OAuth cancellation page (`socialaccount/login_cancelled.html`).
- Added branded Google OAuth confirmation page (`socialaccount/login.html`) because `SOCIALACCOUNT_LOGIN_ON_GET=False` is intentionally retained for safer POST-based initiation.
- Refined Google authentication error page without exposing provider/debug details.
- Unified 400, 403, 404, 429 and 500 pages with the Haybat Al Sultan base layout and responsive state-card pattern.
- Added shared responsive CSS for system/OAuth/error states, including mobile stacking.
- Preserved CSRF POST protection and existing OAuth/security settings.
- Updated static security checker to exclude vendor/generated directories such as `.venv`, `staticfiles`, `node_modules`, caches and media, reducing false positives without excluding application source.

## Review notes
- All user-facing page templates in accounts, socialaccount, catalog, core, orders and management use `base.html`; partials/email templates are intentionally excluded.
- Existing password reset, MFA, profile, Google signup, catalog, checkout and management templates remain on the shared store shell.
- No route, permission, rate-limit, MFA, password-reset, SMTP, pricing, checkout, or data-model behavior was changed by this UI pass.

## Local verification performed in artifact environment
- Python compileall: PASS
- Project static security checker: PASS
- Template inheritance audit: PASS

Run the full Django suite locally before deployment:
`python manage.py test --settings=config.settings.test`

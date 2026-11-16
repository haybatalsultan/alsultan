# SonarQube remediation review — 2026-09-11

This package is based on the uploaded Haybat Al Sultan store source and the 295-issue SonarQube export.

## Implemented in this remediation pass

- Added explicit HTTP method restrictions to public/customer Django views reported by `python:S3752`.
- Preserved the Stripe webhook CSRF exemption only for the Stripe webhook and documented the reviewed exception. The endpoint already verifies `Stripe-Signature` with `STRIPE_WEBHOOK_SECRET` and rejects invalid signatures.
- Fixed the reliability defect in `accounts/forms.py` where both sides of a conditional returned the same placeholder.
- Replaced ModelForm `exclude` declarations reported by `python:S6559` with explicit allow-listed `fields` for address, product and supervisor-permission forms.
- Added explicit constants for repeated Python literals reported by `python:S1192`, including route names, labels, seed-data values and security-check paths.
- Removed/renamed several code-quality findings without changing external APIs: compatibility no-op parameters are explicitly consumed, seed decimal helper renamed, local model variables normalized, and expense category initialization uses `dict.fromkeys`.
- Fixed reported form-label associations and added stable/unique IDs where required.
- Improved semantic/accessibility markup for status regions, product-gallery controls, navigation and search controls while keeping existing CSS classes and behavior.
- Reworked product-gallery JavaScript to use explicit blocks and readable control flow instead of ambiguous single-line conditionals.
- Removed deprecated clipboard fallback based on `document.execCommand`; secure Clipboard API remains, with manual-copy fallback behavior when unavailable.
- Reworked nested wishlist ternaries and removed `void`-based forced reflow in cart UI.
- Replaced deprecated CSS `word-break: break-word` usage with `overflow-wrap:anywhere` + `word-break:normal`.

## Intentionally preserved to avoid regressions

Some Sonar findings are structural/style findings where a blind automated change could alter the visual cascade or email-client compatibility. In particular:

- Repeated CSS selectors in `static/css/store.css`: the later declarations participate in the existing cascade. Merging them without visual regression testing can change the storefront/management UI.
- Layout tables and legacy table attributes in transactional HTML email templates: these remain important for compatibility with Outlook and other email clients. Converting them to modern CSS-only layout without cross-client testing is unsafe.
- Large cognitive-complexity refactors: these require behavior-level Django tests around each flow. They were not mechanically split merely to reduce a Sonar metric.

These retained findings are maintainability/accessibility-style findings rather than unresolved exploitable vulnerabilities. Re-run SonarQube after local functional tests; any remaining issue list can then be addressed with targeted visual/behavior tests.

## Verification performed in the remediation environment

- `python -m compileall -q .` — PASS
- `node --check` for every file under `static/js/*.js` — PASS
- `python scripts/security_static_check.py` — PASS

Full Django tests could not be executed in the remediation environment because third-party Python dependencies are not installed there and outbound package installation is unavailable. Run the normal project test/security suite locally before promoting this package.

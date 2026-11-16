# v20.16.3 — Management UI Polish SECURITY TEST

- Dedicated `management.css` loaded only on `/management/` with cache-busting version.
- Compact management header with fixed logo dimensions; no storefront cart/wishlist shell.
- Responsive desktop/mobile management navigation.
- Simplified page header to remove duplicated owner/session panel.
- Reworked order search/status toolbar while keeping the existing server-side allowlist filter.
- Responsive order cards on mobile.
- Notification settings cards tightened and aligned.
- No permission, MFA, CSRF, order, payment, inventory, or referral business logic changes.
- No migrations.

# MFA QR and cancellation security update

- Owner enrollment now rotates any previous unconfirmed TOTP secret on a fresh primary-login flow.
- QR codes are generated locally in memory; no external QR service receives the provisioning URI.
- Setup keys are collapsed by default and shown only as a manual fallback.
- The provisioning URI is no longer printed in the page.
- Cancel is POST + CSRF and deletes only an unconfirmed MFA device, then flushes the pre-auth session.
- MFA setup and verify responses are marked no-store through `never_cache`.
- OTP POST fields are marked sensitive for Django exception reporting.

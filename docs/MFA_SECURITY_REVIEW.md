# Owner MFA security review

## Policy

- OWNER MFA is mandatory.
- Since v19.6.2, MFA is mandatory for both OWNER and SUPERVISOR management accounts.
- CUSTOMER accounts cannot enroll through the staff MFA setup endpoint.

## Controls implemented

- Password success does not create an authenticated OWNER session until MFA enrollment or verification succeeds.
- Pre-authentication state is server-side session data and expires logically after 10 minutes.
- Session key is rotated when primary authentication succeeds and again after final authentication.
- `/account/mfa/setup/` and `/account/mfa/verify/` are rate-limited in addition to the login endpoint.
- Management routes enforce OWNER MFA as defense in depth for stale or manually-created sessions.
- Owner-only permission checks also require an enabled MFA device.
- TOTP verification uses PyOTP rather than custom cryptography.
- CSRF remains enabled for setup and verification POST requests.
- MFA secrets are never written to security event details or application logs by the MFA implementation.
- The setup secret is rendered only during enrollment and is not rendered after MFA is enabled.

## Known follow-up

A self-service recovery-code workflow is intentionally not included yet. Until a reviewed recovery design exists, losing the Owner authenticator requires a controlled server-side recovery procedure. This is safer than adding a weak bypass path.

# Google Sign-In — HaybatAlsultan

This project uses django-allauth 65.19.1 with the Google OAuth2 provider.

## Environment variables

Add these to `.env` locally and to Render Environment Variables in production:

GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=

Never commit either value.

## Local Google OAuth client configuration

Authorized JavaScript origins:
- http://127.0.0.1:8000
- http://localhost:8000

Authorized redirect URIs:
- http://127.0.0.1:8000/accounts/google/login/callback/
- http://localhost:8000/accounts/google/login/callback/

## Security policy

- Google login is customer-only.
- OWNER and SUPERVISOR accounts cannot use or connect Google social login.
- Existing local accounts are not automatically matched/connected by email.
- OAuth initiation requires POST.
- PKCE is enabled.
- Google access/refresh tokens are not stored.
- New Google signups must complete country, mobile number and policy acceptance.
- Google-provided email is locked on the completion form.
- Regular HaybatAlsultan username/password login remains under `/account/`.
- `/accounts/` is reserved for django-allauth OAuth callbacks and social flows.

## Google testing mode

While the Google OAuth app is in Testing mode, add the Google accounts you want to test under:
Google Auth Platform -> Audience -> Test users.

## Production

When the final canonical production host is chosen, add its HTTPS origin and exact callback URI in Google Cloud, e.g.:

https://www.haybatalsultan.com
https://www.haybatalsultan.com/accounts/google/login/callback/

Use only the actual canonical host in production where practical.

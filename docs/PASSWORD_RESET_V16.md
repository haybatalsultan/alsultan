# Password Reset v16

## Root cause fixed

The project mounts `accounts.urls` with `app_name = "accounts"`.
Django's built-in password-reset views default to un-namespaced URL names:
- `password_reset_done`
- `password_reset_complete`

v16 explicitly configures:
- `success_url=reverse_lazy("accounts:password_reset_done")`
- `success_url=reverse_lazy("accounts:password_reset_complete")`

The reset email also uses the namespaced confirm URL.

## Security behavior

- CSRF remains enabled.
- `/account/password-reset/` remains rate-limited by `SensitiveEndpointRateLimitMiddleware`.
- The success page is generic and does not reveal whether the email exists.
- Django reset tokens remain time-limited and single-use after the password changes.
- Django password validators are applied by the standard SetPasswordForm.
- Google-only accounts with an unusable local password do not receive a Django local-password reset email.

## Local development email

If `EMAIL_HOST` is empty, this project uses Django's console email backend.
The reset email and URL will therefore appear in the terminal running `python manage.py runserver`.

Production must configure SMTP credentials through environment variables.

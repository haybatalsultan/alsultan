# UI, Language & Link Review

Updated in this build:

- Arabic remains RTL; English renders LTR through Django LocaleMiddleware.
- Customer-facing navigation and product/order/account templates now have reviewed English wording.
- Product cards/details use `name_en`, `description_en`, `name_ar`, and `description_ar` according to the active language.
- Main category links now filter the catalog by category slug.
- Footer placeholder `#` links were replaced by real routes for shipping, returns, privacy, terms and FAQ.
- Secure guest order tracking was added using order reference + the same checkout phone number; failures use a generic response.
- Order tracking POST requests are rate-limited.
- Management dashboard recent-order references now link to the real order management page.
- Hero arrows and dots now work and switch between four promotional messages.
- Geolocation messages now follow the active Arabic/English language.
- Footer remains light and includes HaybatAlsultan rights, +971504084006, WhatsApp, Instagram and TikTok.

Verification available in this environment:

- `python -m compileall`: PASS
- `python scripts/security_static_check.py`: PASS
- No remaining `href="#"` placeholders in templates.

Django runtime tests must still be executed in the local VS Code virtual environment because Django is not installed in the build container.

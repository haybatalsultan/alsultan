import re
import sys
from pathlib import Path

ORDERS_WEBHOOKS_PATH = 'orders/webhooks.py'
PRODUCTION_SETTINGS_PATH = 'config/settings/production.py'
MANAGEMENT_VIEWS_PATH = 'core/management_views.py'
LOYALTY_SERVICE_PATH = 'orders/services/loyalty_service.py'

root = Path(__file__).resolve().parents[1]

patterns = {
    "template_safe": re.compile(r"\|safe|mark_safe"),
    "dangerous_eval": re.compile(r"\beval\(|\bexec\("),
    "shell": re.compile(r"os\.system|subprocess\.(?:Popen|run|call).*shell\s*=\s*True"),
    "csrf_exempt": re.compile(r"\bcsrf_exempt\b"),
    "raw_sql": re.compile(r"cursor\.execute|\.raw\("),
    "javascript_url": re.compile(r"""href\s*=\s*["']\s*javascript:""", re.IGNORECASE),
}

issues = []

# Generated/vendor directories are outside the application source review.
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "staticfiles",
    "media",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}

# Stripe webhooks cannot carry Django CSRF tokens. This single endpoint is
# exempt only because it verifies Stripe-Signature using the webhook secret.
CSRF_EXEMPT_ALLOWLIST = {ORDERS_WEBHOOKS_PATH}

for p in root.rglob("*"):
    if any(part in EXCLUDED_PARTS for part in p.relative_to(root).parts):
        continue
    if p.resolve() == Path(__file__).resolve():
        continue
    if p.suffix not in {".py", ".html", ".js"}:
        continue

    rel = str(p.relative_to(root))
    text = p.read_text(encoding="utf-8", errors="ignore")

    # Test fixtures intentionally contain dummy passwords/API keys.
    runtime_file = not rel.startswith("tests/")

    if runtime_file:
        for name, pattern in patterns.items():
            if name == "csrf_exempt" and rel in CSRF_EXEMPT_ALLOWLIST:
                continue
            for match in pattern.finditer(text):
                issues.append(
                    (
                        name,
                        rel,
                        text.count("\n", 0, match.start()) + 1,
                    )
                )

    # Forwarding headers are permitted only in the dedicated security service,
    # where they are explicitly classified as untrusted hints.
    if (
        p.suffix == ".py"
        and runtime_file
        and rel != "accounts/services/security_service.py"
    ):
        for header in ("HTTP_X_FORWARDED_FOR", "HTTP_CF_CONNECTING_IP"):
            if header in text:
                issues.append(("unsafe_forwarded_header_use", rel, header))

# Production security invariants.
production = (root / PRODUCTION_SETTINGS_PATH).read_text(encoding="utf-8")
if "if not REDIS_URL" not in production:
    issues.append(
        ("production_shared_cache_not_required", PRODUCTION_SETTINGS_PATH, 0)
    )
if "RATE_LIMIT_FAIL_CLOSED = True" not in production:
    issues.append(
        ("production_rate_limit_not_fail_closed", PRODUCTION_SETTINGS_PATH, 0)
    )

middleware = (root / "core/middleware.py").read_text(encoding="utf-8")
if "security_digest(label, actor_value)" not in middleware:
    issues.append(("stable_actor_rate_limit_missing", "core/middleware.py", 0))

# v20.7 loyalty/accounting invariants.
management_views = (root / MANAGEMENT_VIEWS_PATH).read_text(encoding="utf-8")
if (
    "def smart_accountant(request):" not in management_views
    or "require_owner(request.user)" not in management_views
):
    issues.append(
        ("smart_accountant_owner_guard_missing", MANAGEMENT_VIEWS_PATH, 0)
    )
if (
    "target in {Order.PaymentStatus.REFUNDED, Order.PaymentStatus.PARTIAL}"
    not in management_views
):
    issues.append(("refund_owner_guard_missing", MANAGEMENT_VIEWS_PATH, 0))

order_models = (root / "orders/models.py").read_text(encoding="utf-8")
for required in (
    "cost_unit_snapshot",
    "cost_total_snapshot",
    "Financial order snapshots are immutable",
):
    if required not in order_models:
        issues.append(
            ("financial_snapshot_guard_missing", "orders/models.py", required)
        )

user_models = (root / "accounts/models.py").read_text(encoding="utf-8")
if re.search(r"\bloyalty_(?:tier|status)\s*=\s*models\.", user_models):
    issues.append(("writable_loyalty_field_detected", "accounts/models.py", 0))

loyalty_service = (root / LOYALTY_SERVICE_PATH).read_text(
    encoding="utf-8"
)
if "status=Order.Status.DELIVERED" not in loyalty_service:
    issues.append(
        ("loyalty_not_delivery_derived", LOYALTY_SERVICE_PATH, 0)
    )

for required_tier in (
    '(10, "ROYAL"',
    '(7, "PLATINUM"',
    '(4, "GOLD"',
    '(2, "SILVER"',
    '(1, "NEW"',
    '(0, "MEMBER"',
):
    if required_tier not in loyalty_service:
        issues.append(
            (
                "loyalty_tier_policy_missing",
                LOYALTY_SERVICE_PATH,
                required_tier,
            )
        )

if "DISTINGUISHED" in loyalty_service:
    issues.append(
        (
            "legacy_distinguished_loyalty_tier_detected",
            LOYALTY_SERVICE_PATH,
            0,
        )
    )

# Stripe webhook exemption is allowed only with signature verification and POST.
stripe_webhook = (root / ORDERS_WEBHOOKS_PATH).read_text(encoding="utf-8")
for required in (
    "@csrf_exempt",
    "@require_POST",
    "stripe.Webhook.construct_event",
    "STRIPE_WEBHOOK_SECRET",
    "Stripe-Signature",
):
    if required not in stripe_webhook:
        issues.append(
            ("stripe_webhook_signature_guard_missing", ORDERS_WEBHOOKS_PATH, required)
        )

# v20.8.1 Quick Sale security invariants.
quick_sale = (root / "orders/services/quick_sale_service.py").read_text(encoding="utf-8")
management = (root / "core/management_views.py").read_text(encoding="utf-8")
if "select_for_update()" not in quick_sale:
    issues.append(("quick_sale_missing_inventory_lock", "orders/services/quick_sale_service.py", 0))
if "price_snapshot(product)" not in quick_sale:
    issues.append(("quick_sale_missing_server_pricing", "orders/services/quick_sale_service.py", 0))
if "IdempotencyRecord.objects.create" not in quick_sale:
    issues.append(("quick_sale_missing_idempotency", "orders/services/quick_sale_service.py", 0))
if "def quick_sale(request):" not in management or "require_owner(request.user)" not in management:
    issues.append(("quick_sale_owner_guard_missing", "core/management_views.py", 0))

# v20.8.1.1 Quick Sale search security invariants.
if "def quick_sale_product_search(request):" not in management:
    issues.append(("quick_sale_search_missing", "core/management_views.py", 0))
for required in (
    "@require_GET",
    "require_owner(request.user)",
    "available_quantity__gt=F(\"reserved_quantity\")",
    ".order_by(\"sku\")[:10]",
):
    if required not in management:
        issues.append(("quick_sale_search_guard_missing", "core/management_views.py", required))

quick_sale_js = (root / "static/js/quick-sale.js").read_text(encoding="utf-8")
if "innerHTML" in quick_sale_js:
    issues.append(("quick_sale_dom_injection_pattern", "static/js/quick-sale.js", "innerHTML"))
if "cost_price" in quick_sale_js:
    issues.append(("quick_sale_cost_exposed_to_browser", "static/js/quick-sale.js", "cost_price"))

# v20.8.1.2 deferred/custody invariants.
orders_models=(root / "orders/models.py").read_text(encoding="utf-8")
catalog_models=(root / "catalog/models.py").read_text(encoding="utf-8")
if 'DEFERRED = "DEFERRED"' not in orders_models or 'DirectPaymentEntryQuerySet' not in orders_models:
    issues.append(("deferred_payment_guards_missing","orders/models.py",0))
if 'ProductCustodyHistoryQuerySet' not in catalog_models or 'append-only' not in catalog_models:
    issues.append(("product_custody_immutability_missing","catalog/models.py",0))
if 'def receivables(request):' not in management or 'def product_custody(request, public_id):' not in management:
    issues.append(("owner_receivable_or_custody_view_missing","core/management_views.py",0))

accountant_service = (root / "orders/services/accountant_service.py").read_text(encoding="utf-8")
if "from orders.models import DirectPaymentEntry" not in accountant_service and "DirectPaymentEntry, Expense" not in accountant_service:
    issues.append(("deferred_payment_accountant_import_missing", "orders/services/accountant_service.py", 0))
if "order__sale_channel=Order.SaleChannel.DIRECT" in accountant_service:
    issues.append(("receivable_collection_channel_filter_detected", "orders/services/accountant_service.py", 0))

# v20.8.1.3 order-detail / hand-to-hand delivery invariants.
order_models_v20813 = (root / "orders/models.py").read_text(encoding="utf-8")
order_detail_view_v20813 = (root / "core/management_views.py").read_text(encoding="utf-8")
quick_sale_v20813 = (root / "orders/services/quick_sale_service.py").read_text(encoding="utf-8")
for required in ("HAND_TO_HAND", "hand_to_hand_at", "hand_to_hand_by"):
    if required not in order_models_v20813:
        issues.append(("hand_to_hand_model_guard_missing", "orders/models.py", required))
for required in (
    'action == "hand_to_hand"',
    'require_permission(request.user, "ship_orders")',
    "Order.objects.select_for_update().get(pk=order.pk)",
    "order_hand_to_hand_delivered",
):
    if required not in order_detail_view_v20813:
        issues.append(("hand_to_hand_server_guard_missing", "core/management_views.py", required))
if "delivery_method=Order.DeliveryMethod.HAND_TO_HAND" not in quick_sale_v20813:
    issues.append(("quick_sale_hand_to_hand_snapshot_missing", "orders/services/quick_sale_service.py", 0))

# v20.8.1.3 FIX1 migration-chain invariant.
hand_to_hand_migration = root / "orders/migrations/0020_order_hand_to_hand_delivery.py"
if not hand_to_hand_migration.exists():
    issues.append(("hand_to_hand_migration_missing", "orders/migrations/0020_order_hand_to_hand_delivery.py", 0))
else:
    migration_text = hand_to_hand_migration.read_text(encoding="utf-8")
    if '("orders", "0019_deferred_payment_receivables")' not in migration_text:
        issues.append(("hand_to_hand_migration_parent_invalid", "orders/migrations/0020_order_hand_to_hand_delivery.py", 0))

# v20.8.1.3 FIX2 model/migration state invariants.
orders_model_state = (root / "orders/models.py").read_text(encoding="utf-8")
catalog_model_state = (root / "catalog/models.py").read_text(encoding="utf-8")
for required in (
    "PARTIALLY_PAID",
    "DEFERRED",
    "payment_due_date = models.DateField",
    "payment_reminder_days = models.PositiveSmallIntegerField",
    "class DirectPaymentEntry(models.Model):",
    "class DeliveryMethod(models.TextChoices):",
    "hand_to_hand_at = models.DateTimeField",
    "hand_to_hand_by = models.ForeignKey",
):
    if required not in orders_model_state:
        issues.append(("orders_model_migration_state_missing", "orders/models.py", required))
if "class ProductCustodyHistory(models.Model):" not in catalog_model_state:
    issues.append(("catalog_custody_model_state_missing", "catalog/models.py", 0))

# v20.8.1.3 FIX3 timeline schema invariant.
management_v20813_fix3 = (root / "core/management_views.py").read_text(encoding="utf-8")
if 'metadata={"delivery_method": "HAND_TO_HAND"' in management_v20813_fix3:
    issues.append(("unsupported_timeline_metadata_kwarg", "core/management_views.py", 0))

# v20.8.1.4 receivable UX/security invariants.
receivable_form_v20814 = (root / "core/forms.py").read_text(encoding="utf-8")
receivable_view_v20814 = (root / "core/management_views.py").read_text(encoding="utf-8")
receivable_js_v20814 = (root / "static/js/receivable-payment.js").read_text(encoding="utf-8")
if "confirm_received = forms.BooleanField(required=True)" not in receivable_form_v20814:
    issues.append(("receivable_confirmation_not_server_required", "core/forms.py", 0))
for required in (
    "Order.objects.select_for_update().get(",
    "payment_method=Order.PaymentMethod.DEFERRED",
    "amount > remaining",
):
    if required not in receivable_view_v20814:
        issues.append(("receivable_server_guard_missing", "core/management_views.py", required))
if "innerHTML" in receivable_js_v20814:
    issues.append(("receivable_dom_injection_pattern", "static/js/receivable-payment.js", 0))

# v20.8.1.4 FIX1 Decimal import invariant.
management_imports_v20814_fix1 = (root / "core/management_views.py").read_text(encoding="utf-8")
if "Decimal(" in management_imports_v20814_fix1 and "from decimal import Decimal" not in management_imports_v20814_fix1:
    issues.append(("decimal_used_without_import", "core/management_views.py", 0))

# v20.8.1.5 custody UX/security invariants.
custody_view_v20815 = (root / "core/management_views.py").read_text(encoding="utf-8")
custody_form_v20815 = (root / "core/forms.py").read_text(encoding="utf-8")
if "def product_custody(request, public_id):" not in custody_view_v20815 or "require_owner(request.user)" not in custody_view_v20815:
    issues.append(("custody_owner_guard_missing", "core/management_views.py", 0))
if "class ProductCustodyForm(forms.Form):" not in custody_form_v20815:
    issues.append(("custody_form_missing", "core/forms.py", 0))

# v20.8.1.6 Haybat order-tracker invariants.
tracking_view_v20816 = (root / "core/management_views.py").read_text(encoding="utf-8")
tracking_template_v20816 = (root / "templates/management/order_detail.html").read_text(encoding="utf-8")
if "tracking_stages = [" not in tracking_view_v20816:
    issues.append(("server_derived_tracking_missing", "core/management_views.py", 0))
if 'name="tracking_stage"' in tracking_template_v20816:
    issues.append(("client_mutable_tracking_state_detected", "templates/management/order_detail.html", 0))

# v20.8.1.6 FIX1 tracker regression invariant.
legacy_tracker_test = (root / "tests/test_order_detail_hand_to_hand_v20_8_1_3.py").read_text(encoding="utf-8")
if 'self.assertContains(response, "order-timeline-horizontal")' in legacy_tracker_test:
    issues.append(("obsolete_timeline_assertion_detected", "tests/test_order_detail_hand_to_hand_v20_8_1_3.py", 0))
if 'self.assertContains(response, "haybat-order-tracker")' not in legacy_tracker_test:
    issues.append(("haybat_tracker_regression_assertion_missing", "tests/test_order_detail_hand_to_hand_v20_8_1_3.py", 0))

# v20.8.2 secure invoice invariants.
invoice_models_v2082 = (root / "orders/models.py").read_text(encoding="utf-8")
invoice_service_v2082 = (root / "orders/services/invoice_service.py").read_text(encoding="utf-8")
invoice_views_v2082 = (root / "core/management_views.py").read_text(encoding="utf-8")
invoice_template_v2082 = (root / "templates/management/invoice_detail.html").read_text(encoding="utf-8")
for required in (
    "class Invoice(models.Model):",
    "class InvoiceItem(models.Model):",
    "Invoices are immutable snapshots.",
    "Invoice items are immutable snapshots.",
):
    if required not in invoice_models_v2082:
        issues.append(("invoice_immutability_guard_missing", "orders/models.py", required))
for forbidden in ("cost_unit_snapshot", "cost_total_snapshot"):
    invoice_item_section = invoice_models_v2082.split("class InvoiceItem(models.Model):", 1)[-1]
    if forbidden in invoice_item_section:
        issues.append(("invoice_owner_cost_field_detected", "orders/models.py", forbidden))
for required in (
    "Order.objects.select_for_update()",
    "build_invoice_number",
    "outstanding_snapshot=outstanding",
):
    if required not in invoice_service_v2082:
        issues.append(("invoice_snapshot_guard_missing", "orders/services/invoice_service.py", required))
for required in (
    "@require_POST\ndef invoice_create",
    "require_owner(request.user)",
    "require_permission(request.user, \"view_orders\")",
    'response["Cache-Control"] = "private, no-store"',
):
    if required not in invoice_views_v2082:
        issues.append(("invoice_access_guard_missing", "core/management_views.py", required))
if "cost_unit" in invoice_template_v2082 or "cost_total" in invoice_template_v2082:
    issues.append(("invoice_cost_exposed_in_template", "templates/management/invoice_detail.html", 0))

# v20.8.2 FIX1 dependency portability invariant.
requirements_v2082_fix1 = (root / "requirements.txt").read_text(encoding="utf-8").lower()
invoice_service_v2082_fix1 = (root / "orders/services/invoice_service.py").read_text(encoding="utf-8")
if "python-bidi" in requirements_v2082_fix1:
    issues.append(("invoice_native_dependency_detected", "requirements.txt", "python-bidi"))
if "from bidi" in invoice_service_v2082_fix1:
    issues.append(("invoice_bidi_runtime_dependency_detected", "orders/services/invoice_service.py", 0))

# v20.8.2.1 premium invoice identity invariants.
invoice_settings_view = (root / "core/management_views.py").read_text(encoding="utf-8")
invoice_settings_form = (root / "core/forms.py").read_text(encoding="utf-8")
invoice_pdf_service = (root / "orders/services/invoice_service.py").read_text(encoding="utf-8")
requirements_premium_invoice = (root / "requirements.txt").read_text(encoding="utf-8").lower()
for required in (
    "def invoice_settings(request):",
    "require_owner(request.user)",
    "InvoiceIdentitySettingsForm",
    "invoice_settings_updated",
):
    if required not in invoice_settings_view:
        issues.append(("invoice_settings_owner_guard_missing", "core/management_views.py", required))
if "validate_image(upload)" not in invoice_settings_form:
    issues.append(("invoice_brand_image_validation_missing", "core/forms.py", 0))
if 'parsed.scheme != "https" or parsed.hostname != "res.cloudinary.com"' not in invoice_pdf_service:
    issues.append(("invoice_pdf_remote_image_ssrf_guard_missing", "orders/services/invoice_service.py", 0))
if "python-bidi" in requirements_premium_invoice:
    issues.append(("rust_bidi_dependency_reintroduced", "requirements.txt", 0))

# v20.8.2.1 FIX1 dependency regression invariant.
invoice_dependency_test = (root / "tests/test_invoice_dependency_v20_8_2_fix1.py").read_text(encoding="utf-8")
if 'self.assertNotIn("arabic-reshaper", requirements)' in invoice_dependency_test:
    issues.append(("obsolete_arabic_reshaper_assertion_detected", "tests/test_invoice_dependency_v20_8_2_fix1.py", 0))
if 'self.assertNotIn("python-bidi", requirements)' not in invoice_dependency_test:
    issues.append(("python_bidi_regression_guard_missing", "tests/test_invoice_dependency_v20_8_2_fix1.py", 0))

# v20.8.2.1 FIX2 Arabic invoice layout/navigation invariants.
invoice_dashboard_fix2 = (root / "templates/management/dashboard.html").read_text(encoding="utf-8")
invoice_preview_fix2 = (root / "templates/management/invoice_detail.html").read_text(encoding="utf-8")
invoice_pdf_fix2 = (root / "orders/services/invoice_service.py").read_text(encoding="utf-8")
if "invoice-settings-tool" not in invoice_dashboard_fix2 or "management_invoice_settings" not in invoice_dashboard_fix2:
    issues.append(("invoice_settings_dashboard_card_missing", "templates/management/dashboard.html", 0))
if 'modern-arabic-invoice" dir="rtl"' not in invoice_preview_fix2:
    issues.append(("invoice_rtl_layout_missing", "templates/management/invoice_detail.html", 0))
if 'sync_playwright' not in invoice_pdf_fix2 or '"management/invoice_pdf_browser.html"' not in invoice_pdf_fix2:
    issues.append(("invoice_pdf_browser_renderer_missing", "orders/services/invoice_service.py", 0))

# v20.8.2.1 FIX2A Arabic invoice regression-test invariant.
arabic_invoice_test = (root / "tests/test_arabic_invoice_layout_v20_8_2_1_fix2.py").read_text(encoding="utf-8")
if 'self.assertNotIn("HAND_TO_HAND", template.split(' in arabic_invoice_test:
    issues.append(("obsolete_template_source_enum_assertion", "tests/test_arabic_invoice_layout_v20_8_2_1_fix2.py", 0))
if 'self.assertIn("استلام يدًا بيد", template)' not in arabic_invoice_test:
    issues.append(("arabic_hand_to_hand_label_assertion_missing", "tests/test_arabic_invoice_layout_v20_8_2_1_fix2.py", 0))

# v20.8.2.1 FIX3 modern invoice visual/security invariants.
modern_invoice_template = (root / "templates/management/invoice_detail.html").read_text(encoding="utf-8")
modern_invoice_service = (root / "orders/services/invoice_service.py").read_text(encoding="utf-8")
if "modern-arabic-invoice" not in modern_invoice_template:
    issues.append(("modern_invoice_layout_missing", "templates/management/invoice_detail.html", 0))
for forbidden in ('name="grand_total', 'name="paid_total', 'name="outstanding'):
    if forbidden in modern_invoice_template:
        issues.append(("invoice_financial_edit_field_detected", "templates/management/invoice_detail.html", forbidden))
if "_trusted_brand_image_bytes" not in modern_invoice_service:
    issues.append(("invoice_remote_image_guard_missing", "orders/services/invoice_service.py", 0))


# v20.8.2.3 browser-rendered PDF invariants.
browser_pdf_service=(root/"orders/services/invoice_service.py").read_text(encoding="utf-8")
browser_pdf_template=(root/"templates/management/invoice_pdf_browser.html").read_text(encoding="utf-8")
browser_pdf_requirements=(root/"requirements.txt").read_text(encoding="utf-8").lower()
if "playwright==1.55.0" not in browser_pdf_requirements:
    issues.append(("playwright_pdf_dependency_missing","requirements.txt",0))
if "xhtml2pdf" in browser_pdf_requirements or "python-bidi" in browser_pdf_requirements:
    issues.append(("obsolete_pdf_dependency_detected","requirements.txt",0))
if 'parsed.scheme != "https" or parsed.hostname != "res.cloudinary.com"' not in browser_pdf_service:
    issues.append(("invoice_pdf_brand_url_guard_missing","orders/services/invoice_service.py",0))
if "page.set_content(html" not in browser_pdf_service or "page.pdf(" not in browser_pdf_service:
    issues.append(("browser_pdf_render_flow_missing","orders/services/invoice_service.py",0))
if 'lang="ar" dir="rtl"' not in browser_pdf_template or "<script" in browser_pdf_template.lower():
    issues.append(("browser_pdf_template_safety_or_rtl_failure","templates/management/invoice_pdf_browser.html",0))

# v20.8.2.3 FIX1 Cairo + embedded branding invariants.
pdf_fix1_service=(root/"orders/services/invoice_service.py").read_text(encoding="utf-8")
pdf_fix1_template=(root/"templates/management/invoice_pdf_browser.html").read_text(encoding="utf-8")
if 'family=Cairo' not in pdf_fix1_template or 'font-family:"Cairo"' not in pdf_fix1_template:
    issues.append(("invoice_pdf_cairo_font_missing","templates/management/invoice_pdf_browser.html",0))
if "_brand_data_uri" not in pdf_fix1_service or "_default_logo_data_uri" not in pdf_fix1_service:
    issues.append(("invoice_pdf_embedded_branding_missing","orders/services/invoice_service.py",0))
if 'host in {"fonts.googleapis.com", "fonts.gstatic.com"}' not in pdf_fix1_service:
    issues.append(("invoice_pdf_font_network_allowlist_missing","orders/services/invoice_service.py",0))
if "document.fonts.ready" not in pdf_fix1_service:
    issues.append(("invoice_pdf_font_wait_missing","orders/services/invoice_service.py",0))

# v20.8.3 complimentary bead-adjustment invariants.
bead_views=(root/"orders/views.py").read_text(encoding="utf-8")
bead_order_service=(root/"orders/services/order_service.py").read_text(encoding="utf-8")
bead_management=(root/"core/management_views.py").read_text(encoding="utf-8")
for required in ("requested < 33","requested > product_count","not store.bead_adjustment_enabled"):
    if required not in bead_views:
        issues.append(("bead_adjustment_server_validation_missing","orders/views.py",required))
for required in ("original_bead_count_snapshot=product.bead_count","requested_bead_count_snapshot=ci.requested_bead_count"):
    if required not in bead_order_service:
        issues.append(("bead_adjustment_snapshot_missing","orders/services/order_service.py",required))
if "def bead_adjustment_settings" not in bead_management or "require_owner(request.user)" not in bead_management:
    issues.append(("bead_adjustment_owner_guard_missing","core/management_views.py",0))

# v20.8.3.1 server-side price safety invariants.
price_form=(root/"core/forms.py").read_text(encoding="utf-8")
for required in ('HIGH_DISCOUNT_WARNING_PERCENT = Decimal("15.00")','percent > self.HIGH_DISCOUNT_WARNING_PERCENT','not cleaned.get("confirm_high_discount")','discount >= selling'):
    if required not in price_form:
        issues.append(("price_safety_guard_missing","core/forms.py",required))

# v20.8.3.1 FIX1 price-guard compatibility invariants.
pricing_view=(root/"core/management_views.py").read_text(encoding="utf-8")
generic_form=(root/"templates/management/form.html").read_text(encoding="utf-8")
if '"management/pricing_form.html"' in pricing_view:
    issues.append(("pricing_template_contract_changed","core/management_views.py",0))
if "data-high-discount-warning" not in generic_form:
    issues.append(("price_guard_ui_missing_from_generic_form","templates/management/form.html",0))

# v20.8.3.2 price transparency invariants.
products_view=(root/"core/management_views.py").read_text(encoding="utf-8")
products_template=(root/"templates/management/products.html").read_text(encoding="utf-8")
if "attach_offer_snapshots(list(queryset))" not in products_view:
    issues.append(("price_audit_not_using_central_engine","core/management_views.py",0))
for required in ("PRODUCT","PROMOTION","HIGH"):
    if required not in products_view:
        issues.append(("price_audit_filter_missing","core/management_views.py",required))
if "price-high-warning" not in products_template or "price-source-chip" not in products_template:
    issues.append(("price_audit_ui_missing","templates/management/products.html",0))

# v20.8.3.3 discount source/history + explicit cleanup invariants.
discount_views=(root/"core/management_views.py").read_text(encoding="utf-8")
discount_forms=(root/"core/forms.py").read_text(encoding="utf-8")
for required in ("def clear_direct_discount","def clear_all_direct_discounts",'request.POST.get("confirm") != "CLEAR_ALL_DIRECT_DISCOUNTS"',"require_owner(request.user)"):
    if required not in discount_views:
        issues.append(("direct_discount_cleanup_guard_missing","core/management_views.py",required))
if 'discount_reason = forms.CharField' not in discount_forms:
    issues.append(("direct_discount_reason_missing","core/forms.py",0))

# v20.8.3.3 FIX1 compatibility invariants.
discount_history_view=(root/"core/management_views.py").read_text(encoding="utf-8")
price_safety_test=(root/"tests/test_price_safety_guard_v20_8_3_1.py").read_text(encoding="utf-8")
pricing_section=discount_history_view.split("def pricing(request, public_id):",1)[-1].split("@staff_required\n@require_POST\ndef clear_direct_discount",1)[0]
if "messages.success(request" in pricing_section:
    issues.append(("pricing_requestfactory_message_regression","core/management_views.py",0))
if '"discount_reason":"اختبار خصم"' not in price_safety_test:
    issues.append(("price_safety_reason_fixture_missing","tests/test_price_safety_guard_v20_8_3_1.py",0))

# v20.8.3.3 FIX2 pricing-history isolation invariant.
discount_history_view=(root/"core/management_views.py").read_text(encoding="utf-8")
pricing_body=discount_history_view.split("def pricing(request, public_id):",1)[-1].split("@staff_required\ndef product_pricing_history",1)[0]
if "AuditLog.objects.filter" in pricing_body:
    issues.append(("pricing_get_unexpected_audit_db_query","core/management_views.py",0))
if "def product_pricing_history" not in discount_history_view:
    issues.append(("dedicated_pricing_history_missing","core/management_views.py",0))

# v20.8.3.3 FIX3 template regression invariant.
management_form=(root/"templates/management/form.html").read_text(encoding="utf-8")
if management_form.count("{% if ") != management_form.count("{% endif %}"):
    issues.append(("management_form_unbalanced_if_tags","templates/management/form.html",0))

# v20.8.3.3 FIX4 cleanup confirmation/result-card invariants.
cleanup_view=(root/"core/management_views.py").read_text(encoding="utf-8")
cleanup_template=(root/"templates/management/products.html").read_text(encoding="utf-8")
for required in ('request.session["discount_cleanup_result"]','"promotions_modified": 0'):
    if required not in cleanup_view:
        issues.append(("discount_cleanup_result_missing","core/management_views.py",required))
for required in ("data-discount-modal","CLEAR_ALL_DIRECT_DISCOUNTS","لم يتم تعديل أي Promotion"):
    if required not in cleanup_template:
        issues.append(("discount_cleanup_confirmation_ui_missing","templates/management/products.html",required))

# v20.8.3.3 FIX5 cleanup result completeness invariant.
cleanup_template_fix5=(root/"templates/management/products.html").read_text(encoding="utf-8")
if "لا توجد خصومات مباشرة حاليًا." not in cleanup_template_fix5:
    issues.append(("discount_cleanup_zero_state_missing","templates/management/products.html",0))

# v20.8.3.4 paid-only invoice invariants.
invoice_guard_view=(root/"core/management_views.py").read_text(encoding="utf-8")
invoice_guard_template=(root/"templates/management/order_detail.html").read_text(encoding="utf-8")
if "{% if order.payment_status == 'PAID' %}" not in invoice_guard_template:
    issues.append(("paid_invoice_ui_guard_missing","templates/management/order_detail.html",0))
if "data-payment-confirm-button disabled" not in invoice_guard_template:
    issues.append(("payment_checklist_disabled_state_missing","templates/management/order_detail.html",0))

for issue in issues:
    print(":".join(map(str, issue)))

if issues:
    sys.exit(1)

print("Static security pattern + project invariant scan: PASS")

from django.conf import settings
from django.db import models

from core.services.checkout_fields import default_checkout_field_config


def default_shipping_countries():
    return ["AE"]


class StoreSetting(models.Model):
    singleton = models.BooleanField(default=True, unique=True)
    store_name_ar = models.CharField(max_length=120, default="هيبة السلطان")
    store_name_en = models.CharField(max_length=120, default="Haybat Al Sultan")
    email = models.EmailField(blank=True)
    currency = models.CharField(max_length=3, default="AED")
    default_country = models.CharField(max_length=2, default="AE")
    allowed_registration_countries = models.JSONField(default=list, blank=True)
    allowed_shipping_countries = models.JSONField(default=default_shipping_countries)
    reservation_minutes = models.PositiveIntegerField(default=30)
    whatsapp_checkout_enabled = models.BooleanField(default=True)
    gift_option_enabled = models.BooleanField(default=True)
    bead_adjustment_enabled = models.BooleanField(default=False)
    location_enabled = models.BooleanField(default=True)
    online_payment_enabled = models.BooleanField(default=False)
    notification_email = models.EmailField(blank=True)
    notify_admin_new_order = models.BooleanField(default=True)
    notify_admin_payment = models.BooleanField(default=True)
    notify_admin_shipping = models.BooleanField(default=False)
    notify_customer_payment = models.BooleanField(default=True)
    notify_customer_shipping = models.BooleanField(default=True)
    checkout_field_config = models.JSONField(
        default=default_checkout_field_config,
        blank=True,
    )
    invoice_language = models.CharField(max_length=8, default="ar")
    invoice_business_name = models.CharField(max_length=120, default="هيبة السلطان")
    invoice_phone = models.CharField(max_length=32, default="+971 50 408 4006")
    invoice_email = models.EmailField(default="info@haybatalsultan.com")
    invoice_address = models.CharField(max_length=220, default="أبوظبي، الإمارات العربية المتحدة")
    invoice_thank_you = models.CharField(max_length=220, default="شكرًا لاختياركم هيبة السلطان")
    invoice_footer_note = models.CharField(max_length=300, blank=True)
    invoice_logo_url = models.URLField(max_length=700, blank=True)
    invoice_logo_public_id = models.CharField(max_length=255, blank=True)
    invoice_stamp_url = models.URLField(max_length=700, blank=True)
    invoice_stamp_public_id = models.CharField(max_length=255, blank=True)
    invoice_stamp_mode = models.CharField(
        max_length=16,
        choices=(("PAID", "Paid only"), ("ALWAYS", "Always"), ("NEVER", "Never")),
        default="PAID",
    )
    invoice_show_phone = models.BooleanField(default=True)
    invoice_show_email = models.BooleanField(default=True)
    invoice_show_order_reference = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)


class Banner(models.Model):
    title_ar = models.CharField(max_length=180)
    title_en = models.CharField(max_length=180, blank=True)
    image_url = models.URLField(max_length=700, blank=True)
    target_url = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)


class ImmutableAuditQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise RuntimeError("Audit logs cannot be updated through application ORM.")

    def delete(self, *args, **kwargs):
        raise RuntimeError("Audit logs cannot be deleted through application ORM.")


class AuditLog(models.Model):
    objects = ImmutableAuditQuerySet.as_manager()

    class Outcome(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"

    class Source(models.TextChoices):
        MANAGEMENT = "MANAGEMENT", "Management"
        STOREFRONT = "STOREFRONT", "Storefront"
        SECURITY = "SECURITY", "Security"
        SYSTEM = "SYSTEM", "System"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_username = models.CharField(max_length=150, blank=True)
    actor_role = models.CharField(max_length=20, blank=True, db_index=True)
    action = models.CharField(max_length=80, db_index=True)
    category = models.CharField(max_length=40, blank=True, db_index=True)
    outcome = models.CharField(
        max_length=16, choices=Outcome.choices, default=Outcome.SUCCESS, db_index=True
    )
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.MANAGEMENT, db_index=True
    )
    object_type = models.CharField(max_length=80, db_index=True)
    object_reference = models.CharField(max_length=100, db_index=True)
    request_id = models.CharField(max_length=64, blank=True, db_index=True)
    http_method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=300, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    integrity_hash = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "created_at"]),
            models.Index(fields=["actor_role", "created_at"]),
            models.Index(fields=["outcome", "created_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError("Audit logs are immutable through application code.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Audit logs cannot be deleted through application code.")

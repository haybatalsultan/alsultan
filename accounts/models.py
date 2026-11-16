import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower

phone_validator = RegexValidator(
    r"^\+[1-9]\d{7,14}$", "Use E.164 format, e.g. +971501234567."
)


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        SUPERVISOR = "SUPERVISOR", "Supervisor"
        CUSTOMER = "CUSTOMER", "Customer"

    public_id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.CUSTOMER, db_index=True
    )
    phone_e164 = models.CharField(
        max_length=16, blank=True, validators=[phone_validator]
    )
    country = models.CharField(max_length=2, default="AE", db_index=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    def save(self, *args, **kwargs):
        if self.pk:
            old = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("role", "is_active", "is_archived")
                .first()
            )
            if (
                old
                and old["role"] == self.Role.OWNER
                and (
                    self.role != self.Role.OWNER
                    or not self.is_active
                    or self.is_archived
                )
            ):
                raise ValueError(
                    "Owner role/status cannot be changed through application code."
                )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_owner:
            raise ValueError(
                "Owner accounts cannot be deleted through application code."
            )
        return super().delete(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role"],
                condition=models.Q(role="OWNER"),
                name="single_owner_role",
            ),
            models.UniqueConstraint(
                Lower("email"),
                condition=~models.Q(email=""),
                name="unique_user_email_ci",
            ),
        ]


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=60, blank=True)
    country = models.CharField(max_length=2, default="AE")
    emirate = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=120, blank=True)
    area = models.CharField(max_length=120)
    street = models.CharField(max_length=160, blank=True)
    building = models.CharField(max_length=120, blank=True)
    apartment_or_villa = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=24, blank=True)
    additional_notes = models.CharField(max_length=500, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="one_default_address_per_user",
            )
        ]


class SupervisorPermission(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="supervisor_permissions"
    )
    view_products = models.BooleanField(default=False)
    manage_master_data = models.BooleanField(default=False)
    create_products = models.BooleanField(default=False)
    edit_products = models.BooleanField(default=False)
    archive_products = models.BooleanField(default=False)
    manage_product_images = models.BooleanField(default=False)
    view_inventory = models.BooleanField(default=False)
    adjust_inventory = models.BooleanField(default=False)
    view_inventory_history = models.BooleanField(default=False)
    view_orders = models.BooleanField(default=False)
    view_order_timeline = models.BooleanField(default=False)
    view_abandoned_carts = models.BooleanField(default=False)
    confirm_orders = models.BooleanField(default=False)
    extend_reservations = models.BooleanField(default=False)
    prepare_orders = models.BooleanField(default=False)
    ship_orders = models.BooleanField(default=False)
    cancel_orders = models.BooleanField(default=False)
    mark_payment_pending = models.BooleanField(default=False)
    mark_paid = models.BooleanField(default=False)
    view_customers = models.BooleanField(default=False)
    edit_customers = models.BooleanField(default=False)
    contact_customers = models.BooleanField(default=False)
    view_reports = models.BooleanField(default=False)
    export_reports = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)


class MFADevice(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="mfa_device"
    )
    secret = models.CharField(max_length=64)
    enabled = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)


class ImmutableSecurityEventQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise RuntimeError("Security events cannot be updated through application ORM.")

    def delete(self, *args, **kwargs):
        raise RuntimeError("Security events cannot be deleted through application ORM.")


class SecurityEvent(models.Model):
    objects = ImmutableSecurityEventQuerySet.as_manager()
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_events",
    )
    event = models.CharField(max_length=80, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError(
                "Security events are immutable through application code."
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError(
            "Security events cannot be deleted through application code."
        )

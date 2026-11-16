import uuid

import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]
    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "public_id",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, unique=True
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("OWNER", "Owner"),
                            ("SUPERVISOR", "Supervisor"),
                            ("CUSTOMER", "Customer"),
                        ],
                        db_index=True,
                        default="CUSTOMER",
                        max_length=20,
                    ),
                ),
                (
                    "phone_e164",
                    models.CharField(
                        blank=True,
                        max_length=16,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^\\+[1-9]\\d{7,14}$",
                                "Use E.164 format, e.g. +971501234567.",
                            )
                        ],
                    ),
                ),
                ("is_archived", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={"abstract": False},
            managers=[("objects", django.contrib.auth.models.UserManager())],
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(("role", "OWNER")),
                fields=("role",),
                name="single_owner_role",
            ),
        ),
        migrations.CreateModel(
            name="Address",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("label", models.CharField(blank=True, max_length=60)),
                ("country", models.CharField(default="AE", max_length=2)),
                ("emirate", models.CharField(blank=True, max_length=40)),
                ("area", models.CharField(max_length=120)),
                ("street", models.CharField(blank=True, max_length=160)),
                ("building", models.CharField(blank=True, max_length=120)),
                ("apartment_or_villa", models.CharField(blank=True, max_length=120)),
                ("additional_notes", models.CharField(blank=True, max_length=500)),
                (
                    "latitude",
                    models.DecimalField(
                        blank=True, decimal_places=6, max_digits=9, null=True
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        blank=True, decimal_places=6, max_digits=9, null=True
                    ),
                ),
                ("is_default", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="addresses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MFADevice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("secret", models.CharField(max_length=64)),
                ("enabled", models.BooleanField(default=False)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mfa_device",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SecurityEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("event", models.CharField(db_index=True, max_length=80)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=300)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="security_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="SupervisorPermission",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("view_products", models.BooleanField(default=True)),
                ("create_products", models.BooleanField(default=False)),
                ("edit_products", models.BooleanField(default=False)),
                ("archive_products", models.BooleanField(default=False)),
                ("manage_product_images", models.BooleanField(default=False)),
                ("view_inventory", models.BooleanField(default=True)),
                ("adjust_inventory", models.BooleanField(default=False)),
                ("view_inventory_history", models.BooleanField(default=False)),
                ("view_orders", models.BooleanField(default=True)),
                ("confirm_orders", models.BooleanField(default=False)),
                ("prepare_orders", models.BooleanField(default=False)),
                ("ship_orders", models.BooleanField(default=False)),
                ("cancel_orders", models.BooleanField(default=False)),
                ("mark_payment_pending", models.BooleanField(default=False)),
                ("mark_paid", models.BooleanField(default=False)),
                ("view_customers", models.BooleanField(default=False)),
                ("edit_customers", models.BooleanField(default=False)),
                ("contact_customers", models.BooleanField(default=False)),
                ("view_reports", models.BooleanField(default=False)),
                ("export_reports", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="supervisor_permissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]

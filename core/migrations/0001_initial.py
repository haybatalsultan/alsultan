import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import core.models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="StoreSetting",
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
                ("singleton", models.BooleanField(default=True, unique=True)),
                (
                    "store_name_ar",
                    models.CharField(default="هيبة السلطان", max_length=120),
                ),
                (
                    "store_name_en",
                    models.CharField(default="Haybat Al Sultan", max_length=120),
                ),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("currency", models.CharField(default="AED", max_length=3)),
                ("default_country", models.CharField(default="AE", max_length=2)),
                (
                    "allowed_registration_countries",
                    models.JSONField(blank=True, default=list),
                ),
                (
                    "allowed_shipping_countries",
                    models.JSONField(default=core.models.default_shipping_countries),
                ),
                ("reservation_minutes", models.PositiveIntegerField(default=30)),
                ("whatsapp_checkout_enabled", models.BooleanField(default=True)),
                ("gift_option_enabled", models.BooleanField(default=True)),
                ("location_enabled", models.BooleanField(default=True)),
                ("online_payment_enabled", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Banner",
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
                ("title_ar", models.CharField(max_length=180)),
                ("title_en", models.CharField(blank=True, max_length=180)),
                ("image_url", models.URLField(blank=True, max_length=700)),
                ("target_url", models.CharField(blank=True, max_length=300)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="AuditLog",
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
                ("action", models.CharField(db_index=True, max_length=80)),
                ("object_type", models.CharField(max_length=80)),
                ("object_reference", models.CharField(db_index=True, max_length=100)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("old_values", models.JSONField(blank=True, default=dict)),
                ("new_values", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]

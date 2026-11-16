import uuid
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0007_product_automatic_sku"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="has_certificate",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="product",
            name="certificate_issuer",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="product",
            name="certificate_number",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="product",
            name="certificate_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="certificate_notes_ar",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="product",
            name="certificate_notes_en",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="product",
            name="certificate_public",
            field=models.BooleanField(default=True),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(("has_certificate", True))
                | models.Q(("certificate_public", False)),
                name="cert_public_requires_cert",
            ),
        ),
        migrations.CreateModel(
            name="Promotion",
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
                (
                    "public_id",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, unique=True
                    ),
                ),
                ("name_ar", models.CharField(max_length=180)),
                ("name_en", models.CharField(max_length=180)),
                (
                    "scope",
                    models.CharField(
                        choices=[
                            ("ALL", "All products"),
                            ("PRODUCTS", "Selected products"),
                            ("CATEGORIES", "Selected categories"),
                        ],
                        db_index=True,
                        default="PRODUCTS",
                        max_length=16,
                    ),
                ),
                (
                    "discount_type",
                    models.CharField(
                        choices=[
                            ("PERCENT", "Percentage"),
                            ("FIXED", "Fixed amount"),
                            ("NONE", "Gift only"),
                        ],
                        default="PERCENT",
                        max_length=16,
                    ),
                ),
                (
                    "discount_value",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=12,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.00"))
                        ],
                    ),
                ),
                ("gift_name_ar", models.CharField(blank=True, max_length=180)),
                ("gift_name_en", models.CharField(blank=True, max_length=180)),
                ("gift_quantity", models.PositiveSmallIntegerField(default=1)),
                ("starts_at", models.DateTimeField(db_index=True)),
                ("ends_at", models.DateTimeField(db_index=True)),
                (
                    "priority",
                    models.PositiveSmallIntegerField(db_index=True, default=100),
                ),
                ("is_active", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "categories",
                    models.ManyToManyField(
                        blank=True, related_name="promotions", to="catalog.category"
                    ),
                ),
                (
                    "products",
                    models.ManyToManyField(
                        blank=True, related_name="promotions", to="catalog.product"
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="promotions_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="promotions_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-is_active", "priority", "-created_at"],
                "indexes": [
                    models.Index(
                        fields=["is_active", "starts_at", "ends_at"],
                        name="promo_active_time_idx",
                    )
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("discount_value__gte", 0)),
                        name="promotion_discount_gte_0",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("gift_quantity__gte", 1)),
                        name="promotion_gift_qty_gte_1",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("ends_at__gt", models.F("starts_at"))),
                        name="promotion_valid_time_window",
                    ),
                    models.CheckConstraint(
                        condition=~models.Q(("discount_type", "PERCENT"))
                        | models.Q(("discount_value__lte", 90)),
                        name="promotion_percent_lte_90",
                    ),
                    models.CheckConstraint(
                        condition=~models.Q(("discount_type", "NONE"))
                        | models.Q(("discount_value", 0)),
                        name="promotion_gift_only_zero_discount",
                    ),
                ],
            },
        ),
    ]

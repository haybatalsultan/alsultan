import uuid
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0016_checkoutreservationguard"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Expense",
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
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("BOXES", "Boxes"),
                            ("BAGS", "Bags"),
                            ("PACKAGING", "Packaging materials"),
                            ("CARDS_LABELS", "Cards & labels"),
                            ("SHIPPING_DELIVERY", "Shipping & delivery"),
                            ("MARKETING", "Marketing"),
                            ("SUBSCRIPTIONS", "Subscriptions & services"),
                            ("PAYMENT_FEES", "Payment fees"),
                            ("OFFICE", "Office & operations"),
                            ("OTHER", "Other"),
                        ],
                        db_index=True,
                        max_length=32,
                    ),
                ),
                ("description", models.CharField(max_length=200)),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                    ),
                ),
                ("incurred_on", models.DateField(db_index=True)),
                ("supplier", models.CharField(blank=True, max_length=120)),
                (
                    "invoice_reference",
                    models.CharField(blank=True, db_index=True, max_length=80),
                ),
                ("notes", models.CharField(blank=True, max_length=500)),
                (
                    "status",
                    models.CharField(
                        choices=[("ACTIVE", "Active"), ("VOIDED", "Voided")],
                        db_index=True,
                        default="ACTIVE",
                        max_length=16,
                    ),
                ),
                ("void_reason", models.CharField(blank=True, max_length=300)),
                ("voided_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_expenses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="expenses",
                        to="orders.order",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="updated_expenses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "voided_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="voided_expenses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-incurred_on", "-created_at"]},
        ),
        migrations.AddIndex(
            model_name="expense",
            index=models.Index(
                fields=["status", "incurred_on"], name="expense_status_date_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="expense",
            index=models.Index(
                fields=["category", "incurred_on"], name="expense_category_date_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="expense",
            constraint=models.CheckConstraint(
                condition=models.Q(("amount__gt", 0)), name="expense_amount_gt_zero"
            ),
        ),
        migrations.AddConstraint(
            model_name="expense",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        ("status", "ACTIVE"),
                        ("voided_at__isnull", True),
                        ("voided_by__isnull", True),
                        ("void_reason", ""),
                    )
                    | (
                        models.Q(
                            ("status", "VOIDED"),
                            ("voided_at__isnull", False),
                            ("voided_by__isnull", False),
                        )
                        & ~models.Q(("void_reason", ""))
                    )
                ),
                name="expense_void_state_consistent",
            ),
        ),
    ]

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0008_orderitem_financial_snapshots")]
    operations = [
        migrations.CreateModel(
            name="StripeWebhookEvent",
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
                ("event_id", models.CharField(max_length=255, unique=True)),
                ("event_type", models.CharField(db_index=True, max_length=120)),
                (
                    "processed_at",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PaymentAttempt",
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
                    "attempt_key",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "checkout_session_id",
                    models.CharField(
                        blank=True, max_length=255, null=True, unique=True
                    ),
                ),
                (
                    "payment_intent_id",
                    models.CharField(blank=True, db_index=True, max_length=255),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("CREATING", "Creating"),
                            ("OPEN", "Open"),
                            ("PROCESSING", "Processing"),
                            ("PAID", "Paid"),
                            ("FAILED", "Failed"),
                            ("EXPIRED", "Expired"),
                            ("PARTIAL", "Partially refunded"),
                            ("REFUNDED", "Refunded"),
                        ],
                        db_index=True,
                        default="CREATING",
                        max_length=16,
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="AED", max_length=3)),
                (
                    "expires_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="payment_attempts",
                        to="orders.order",
                    ),
                ),
            ],
        ),
    ]

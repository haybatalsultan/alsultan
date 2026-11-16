from decimal import Decimal

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import ambassadors.models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("accounts", "0006_supervisor_order_tracking_permissions"),
        ("orders", "0008_orderitem_financial_snapshots"),
    ]
    operations = [
        migrations.CreateModel(
            name="AmbassadorProgramSetting",
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
                ("enabled", models.BooleanField(db_index=True, default=False)),
                ("earn_aed_block", models.PositiveIntegerField(default=1000)),
                ("earn_points_per_block", models.PositiveIntegerField(default=25)),
                ("redeem_points_block", models.PositiveIntegerField(default=1000)),
                (
                    "redeem_aed_per_block",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("25.00"), max_digits=8
                    ),
                ),
                ("validity_months", models.PositiveSmallIntegerField(default=12)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="AmbassadorProfile",
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
                    "code",
                    models.CharField(
                        db_index=True,
                        default=ambassadors.models.generate_ambassador_code,
                        editable=False,
                        max_length=16,
                        unique=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ambassador_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Referral",
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
                ("code_snapshot", models.CharField(max_length=16)),
                (
                    "eligible_amount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                ("points_awarded", models.PositiveIntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("AWARDED", "Awarded"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=12,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("awarded_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                (
                    "ambassador",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="referrals",
                        to="ambassadors.ambassadorprofile",
                    ),
                ),
                (
                    "order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ambassador_referral",
                        to="orders.order",
                    ),
                ),
                (
                    "referred_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ambassador_referrals_received",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Redemption",
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
                    "kind",
                    models.CharField(
                        choices=[
                            ("DISCOUNT", "Purchase discount"),
                            ("GIFT", "Gift request"),
                        ],
                        db_index=True,
                        max_length=12,
                    ),
                ),
                ("points_used", models.PositiveIntegerField(default=0)),
                (
                    "amount_aed",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0.00"), max_digits=10
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("REQUESTED", "Requested"),
                            ("APPLIED", "Applied"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        db_index=True,
                        default="REQUESTED",
                        max_length=12,
                    ),
                ),
                ("note", models.CharField(blank=True, max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ambassador_redemptions",
                        to="orders.order",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="redemptions",
                        to="ambassadors.ambassadorprofile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PointLedger",
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
                    "kind",
                    models.CharField(
                        choices=[
                            ("EARN", "Referral earned"),
                            ("REDEEM", "Redeemed"),
                            ("EXPIRE", "Expired"),
                            ("ADJUST", "Owner adjustment"),
                        ],
                        db_index=True,
                        max_length=12,
                    ),
                ),
                ("points", models.IntegerField()),
                ("note", models.CharField(blank=True, max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ledger_entries",
                        to="ambassadors.ambassadorprofile",
                    ),
                ),
                (
                    "redemption",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="ambassadors.redemption",
                    ),
                ),
                (
                    "referral",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="ambassadors.referral",
                    ),
                ),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="PointBatch",
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
                ("earned_points", models.PositiveIntegerField()),
                ("remaining_points", models.PositiveIntegerField()),
                (
                    "earned_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now
                    ),
                ),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="point_batches",
                        to="ambassadors.ambassadorprofile",
                    ),
                ),
                (
                    "referral",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="point_batch",
                        to="ambassadors.referral",
                    ),
                ),
            ],
            options={"ordering": ["expires_at", "id"]},
        ),
        migrations.CreateModel(
            name="RedemptionAllocation",
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
                ("points", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="redemption_allocations",
                        to="ambassadors.pointbatch",
                    ),
                ),
                (
                    "redemption",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="allocations",
                        to="ambassadors.redemption",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="redemptionallocation",
            constraint=models.UniqueConstraint(
                fields=("redemption", "batch"),
                name="unique_redemption_batch_allocation",
            ),
        ),
        migrations.AddConstraint(
            model_name="pointbatch",
            constraint=models.CheckConstraint(
                condition=models.Q(remaining_points__lte=models.F("earned_points")),
                name="amb_points_remaining_lte_earned",
            ),
        ),
    ]

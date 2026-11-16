import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


IMMUTABLE_LEDGER_MESSAGE = 'Ambassador point ledger entries are immutable.'

def generate_ambassador_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "HSA-" + "".join(secrets.choice(alphabet) for _ in range(8))


class AmbassadorProgramSetting(models.Model):
    singleton = models.BooleanField(default=True, unique=True)
    enabled = models.BooleanField(default=False, db_index=True)
    earn_aed_block = models.PositiveIntegerField(default=1000)
    earn_points_per_block = models.PositiveIntegerField(default=25)
    redeem_points_block = models.PositiveIntegerField(default=1000)
    redeem_aed_per_block = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("25.00")
    )
    validity_months = models.PositiveSmallIntegerField(default=12)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(singleton=True)
        return obj


class AmbassadorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ambassador_profile",
    )
    code = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        default=generate_ambassador_code,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Referral(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        MANUAL_REVIEW = "REVIEW", "Manual review"
        REJECTED = "REJECTED", "Rejected"
        AWARDED = "AWARDED", "Awarded"
        CANCELLED = "CANCELLED", "Cancelled"

    order = models.OneToOneField(
        "orders.Order", on_delete=models.PROTECT, related_name="ambassador_referral"
    )
    ambassador = models.ForeignKey(
        AmbassadorProfile, on_delete=models.PROTECT, related_name="referrals"
    )
    referred_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ambassador_referrals_received",
    )
    code_snapshot = models.CharField(max_length=16)
    eligible_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    points_awarded = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    awarded_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    review_reason = models.CharField(max_length=40, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)


class PointBatch(models.Model):
    profile = models.ForeignKey(
        AmbassadorProfile, on_delete=models.PROTECT, related_name="point_batches"
    )
    referral = models.OneToOneField(
        Referral, on_delete=models.PROTECT, related_name="point_batch"
    )
    earned_points = models.PositiveIntegerField()
    remaining_points = models.PositiveIntegerField()
    earned_at = models.DateTimeField(default=timezone.now, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["expires_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(remaining_points__lte=models.F("earned_points")),
                name="amb_points_remaining_lte_earned",
            ),
        ]


class Redemption(models.Model):
    class Kind(models.TextChoices):
        DISCOUNT = "DISCOUNT", "Purchase discount"
        GIFT = "GIFT", "Gift request"

    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        APPLIED = "APPLIED", "Applied"
        CANCELLED = "CANCELLED", "Cancelled"

    profile = models.ForeignKey(
        AmbassadorProfile, on_delete=models.PROTECT, related_name="redemptions"
    )
    kind = models.CharField(max_length=12, choices=Kind.choices, db_index=True)
    points_used = models.PositiveIntegerField(default=0)
    amount_aed = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ambassador_redemptions",
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.REQUESTED, db_index=True
    )
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)


class RedemptionAllocation(models.Model):
    redemption = models.ForeignKey(
        Redemption, on_delete=models.PROTECT, related_name="allocations"
    )
    batch = models.ForeignKey(
        PointBatch, on_delete=models.PROTECT, related_name="redemption_allocations"
    )
    points = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["redemption", "batch"],
                name="unique_redemption_batch_allocation",
            )
        ]


class ImmutablePointLedgerQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise RuntimeError(IMMUTABLE_LEDGER_MESSAGE)

    def delete(self, *args, **kwargs):
        raise RuntimeError(IMMUTABLE_LEDGER_MESSAGE)


class PointLedger(models.Model):
    objects = ImmutablePointLedgerQuerySet.as_manager()

    class Kind(models.TextChoices):
        EARN = "EARN", "Referral earned"
        REDEEM = "REDEEM", "Redeemed"
        EXPIRE = "EXPIRE", "Expired"
        ADJUST = "ADJUST", "Owner adjustment"

    profile = models.ForeignKey(
        AmbassadorProfile, on_delete=models.PROTECT, related_name="ledger_entries"
    )
    kind = models.CharField(max_length=12, choices=Kind.choices, db_index=True)
    points = models.IntegerField()
    referral = models.ForeignKey(
        Referral, on_delete=models.PROTECT, null=True, blank=True
    )
    redemption = models.ForeignKey(
        Redemption, on_delete=models.PROTECT, null=True, blank=True
    )
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError(IMMUTABLE_LEDGER_MESSAGE)
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError(IMMUTABLE_LEDGER_MESSAGE)

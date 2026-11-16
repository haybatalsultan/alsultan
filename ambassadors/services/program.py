from calendar import monthrange
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from ambassadors.models import (
    AmbassadorProfile,
    AmbassadorProgramSetting,
    PointBatch,
    PointLedger,
    Redemption,
    RedemptionAllocation,
    Referral,
)


SELF_REFERRAL_MESSAGE = 'لا يمكن استخدام رمز سفيرك الشخصي على طلبك.'

def settings_obj():
    return AmbassadorProgramSetting.load()


def ensure_profile(user):
    if not user or not user.is_authenticated or getattr(user, "role", "") != "CUSTOMER":
        return None
    profile, _ = AmbassadorProfile.objects.get_or_create(user=user)
    return profile


def add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def expire_due_batches(profile=None):
    now = timezone.now()
    qs = PointBatch.objects.select_for_update().filter(
        remaining_points__gt=0, expires_at__lte=now
    )
    if profile:
        qs = qs.filter(profile=profile)
    expired = 0
    for batch in qs:
        points = batch.remaining_points
        batch.remaining_points = 0
        batch.save(update_fields=["remaining_points"])
        PointLedger.objects.create(
            profile=batch.profile,
            kind=PointLedger.Kind.EXPIRE,
            points=-points,
            referral=batch.referral,
            note="Automatic 12-month expiry",
        )
        expired += points
    return expired


def available_points(profile):
    # Read-only balance calculation: expired batches are excluded immediately.
    # Physical zeroing + expiry ledger entries happen on the next points mutation.
    return int(
        profile.point_batches.filter(
            remaining_points__gt=0, expires_at__gt=timezone.now()
        ).aggregate(v=Sum("remaining_points"))["v"]
        or 0
    )


def points_for_amount(amount, cfg=None):
    cfg = cfg or settings_obj()
    if cfg.earn_aed_block <= 0 or cfg.earn_points_per_block <= 0:
        raise RuntimeError("Invalid ambassador earning configuration.")
    amount = Decimal(amount or 0)
    blocks = int(amount // Decimal(cfg.earn_aed_block))
    return max(0, blocks * cfg.earn_points_per_block)


def discount_for_points(points, cfg=None):
    cfg = cfg or settings_obj()
    if cfg.redeem_points_block <= 0 or cfg.redeem_aed_per_block <= 0:
        raise RuntimeError("Invalid ambassador redemption configuration.")
    points = int(points or 0)
    blocks = points // cfg.redeem_points_block
    return (Decimal(blocks) * cfg.redeem_aed_per_block).quantize(Decimal("0.01"))


def evaluate_referral_eligibility(*, referral, order):
    """Return a server-side referral eligibility decision.

    Guest identity is self-asserted and therefore cannot safely prove that the
    buyer is independent from the ambassador. Guest referrals are retained for
    attribution but require owner review before any monetary-value points can be
    awarded. Authenticated referrals are eligible only when the account differs
    from the ambassador account.
    """
    ambassador_user_id = referral.ambassador.user_id
    if order.user_id and order.user_id == ambassador_user_id:
        return Referral.Status.REJECTED, "SELF_REFERRAL_ACCOUNT"
    if referral.referred_user_id and referral.referred_user_id == ambassador_user_id:
        return Referral.Status.REJECTED, "SELF_REFERRAL_ACCOUNT"
    if not order.user_id or not referral.referred_user_id:
        return Referral.Status.MANUAL_REVIEW, "GUEST_IDENTITY_UNVERIFIED"
    return Referral.Status.PENDING, ""


def create_pending_referral(*, order, code, buyer):
    cfg = settings_obj()
    code = (code or "").strip().upper()
    if not cfg.enabled or not code:
        return None
    profile = (
        AmbassadorProfile.objects.select_related("user")
        .filter(code__iexact=code)
        .first()
    )
    if not profile:
        raise ValueError("رمز سفير هيبة السلطان غير صحيح.")
    owner_phone = (profile.user.phone_e164 or "").strip()
    owner_email = (profile.user.email or "").strip().casefold()
    if owner_phone and owner_phone == (order.customer_phone or "").strip():
        raise ValueError(SELF_REFERRAL_MESSAGE)
    if owner_email and owner_email == (order.customer_email or "").strip().casefold():
        raise ValueError(SELF_REFERRAL_MESSAGE)
    if buyer and buyer.is_authenticated and profile.user_id == buyer.id:
        raise ValueError(SELF_REFERRAL_MESSAGE)
    if order.user_id and profile.user_id == order.user_id:
        raise ValueError(SELF_REFERRAL_MESSAGE)
    eligible = max(
        Decimal("0.00"), Decimal(order.subtotal) - Decimal(order.discount_total)
    )
    return Referral.objects.create(
        order=order,
        ambassador=profile,
        referred_user=buyer if buyer and buyer.is_authenticated else None,
        code_snapshot=profile.code,
        eligible_amount=eligible,
        status=Referral.Status.PENDING,
    )


@transaction.atomic
def reconcile_referral(order, *, owner_approved=False):
    referral = (
        Referral.objects.select_for_update()
        .filter(order=order)
        .select_related("ambassador")
        .first()
    )
    if not referral:
        return None
    reversal_required = order.status in {
        "CANCELLED",
        "RETURNED",
    } or order.payment_status in {"REFUNDED", "PARTIAL"}
    if referral.status == Referral.Status.AWARDED and reversal_required:
        batch = PointBatch.objects.select_for_update().filter(referral=referral).first()
        reversible = 0
        if batch and batch.remaining_points > 0:
            reversible = batch.remaining_points
            batch.remaining_points = 0
            batch.save(update_fields=["remaining_points"])
            PointLedger.objects.create(
                profile=referral.ambassador,
                kind=PointLedger.Kind.ADJUST,
                points=-reversible,
                referral=referral,
                note=f"Reversal after {order.status}/{order.payment_status}",
            )
        referral.status = Referral.Status.CANCELLED
        referral.cancelled_at = timezone.now()
        referral.save(update_fields=["status", "cancelled_at"])
        return referral
    if referral.status == Referral.Status.AWARDED:
        return referral
    if reversal_required:
        referral.status = Referral.Status.CANCELLED
        referral.cancelled_at = timezone.now()
        referral.save(update_fields=["status", "cancelled_at"])
        return referral
    if referral.status in {Referral.Status.REJECTED, Referral.Status.MANUAL_REVIEW}:
        return referral
    if order.status != "DELIVERED" or order.payment_status != "PAID":
        return referral

    decision, reason = evaluate_referral_eligibility(referral=referral, order=order)
    if owner_approved and decision == Referral.Status.MANUAL_REVIEW:
        decision, reason = Referral.Status.PENDING, "OWNER_APPROVED"
    if decision == Referral.Status.REJECTED:
        referral.status = Referral.Status.REJECTED
        referral.review_reason = reason
        referral.reviewed_at = timezone.now()
        referral.save(update_fields=["status", "review_reason", "reviewed_at"])
        return referral
    if decision == Referral.Status.MANUAL_REVIEW:
        referral.status = Referral.Status.MANUAL_REVIEW
        referral.review_reason = reason
        referral.save(update_fields=["status", "review_reason"])
        return referral

    cfg = settings_obj()
    points = points_for_amount(referral.eligible_amount, cfg)
    referral.points_awarded = points
    referral.status = Referral.Status.AWARDED
    referral.awarded_at = timezone.now()
    referral.save(update_fields=["points_awarded", "status", "awarded_at"])
    if points:
        earned_at = timezone.now()
        batch = PointBatch.objects.create(
            profile=referral.ambassador,
            referral=referral,
            earned_points=points,
            remaining_points=points,
            earned_at=earned_at,
            expires_at=add_months(earned_at, cfg.validity_months),
        )
        PointLedger.objects.create(
            profile=referral.ambassador,
            kind=PointLedger.Kind.EARN,
            points=points,
            referral=referral,
            note=f"Order {order.reference}",
        )
        return batch
    return referral


@transaction.atomic
def consume_points(profile, points, *, redemption):
    points = int(points)
    if points <= 0:
        raise ValueError("Invalid points amount.")
    expire_due_batches(profile)
    remaining = points
    batches = (
        profile.point_batches.select_for_update()
        .filter(remaining_points__gt=0, expires_at__gt=timezone.now())
        .order_by("expires_at", "id")
    )
    total = sum(b.remaining_points for b in batches)
    if total < points:
        raise ValueError("رصيد النقاط غير كافٍ.")
    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch.remaining_points, remaining)
        batch.remaining_points -= take
        batch.save(update_fields=["remaining_points"])
        RedemptionAllocation.objects.create(
            redemption=redemption, batch=batch, points=take
        )
        remaining -= take
    PointLedger.objects.create(
        profile=profile,
        kind=PointLedger.Kind.REDEEM,
        points=-points,
        redemption=redemption,
        note=redemption.get_kind_display(),
    )


@transaction.atomic
def reconcile_order_redemptions(order):
    if order.status not in {"CANCELLED", "RETURNED"} and order.payment_status not in {
        "REFUNDED",
        "PARTIAL",
    }:
        return 0
    restored = 0
    redemptions = (
        Redemption.objects.select_for_update()
        .filter(
            order=order, kind=Redemption.Kind.DISCOUNT, status=Redemption.Status.APPLIED
        )
        .select_related("profile")
    )
    for redemption in redemptions:
        allocations = (
            redemption.allocations.select_related("batch").select_for_update().all()
        )
        restored_for_redemption = 0
        for allocation in allocations:
            batch = allocation.batch
            capacity = max(0, batch.earned_points - batch.remaining_points)
            give_back = min(allocation.points, capacity)
            if give_back:
                batch.remaining_points += give_back
                batch.save(update_fields=["remaining_points"])
                restored_for_redemption += give_back
        redemption.status = Redemption.Status.CANCELLED
        redemption.resolved_at = timezone.now()
        redemption.note = (redemption.note + " | restored after order reversal")[:300]
        redemption.save(update_fields=["status", "resolved_at", "note"])
        if restored_for_redemption:
            PointLedger.objects.create(
                profile=redemption.profile,
                kind=PointLedger.Kind.ADJUST,
                points=restored_for_redemption,
                redemption=redemption,
                note=f"Restored after order {order.reference} reversal",
            )
        restored += restored_for_redemption
    return restored

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from accounts.models import User
from core.services.audit_service import audit

from .models import PointLedger, Redemption, Referral
from .services.program import (
    available_points,
    discount_for_points,
    ensure_profile,
    points_for_amount,
    settings_obj,
)


AMBASSADOR_ACCOUNT_URL = 'ambassadors:account'

@login_required
@require_GET
def account(request):
    if request.user.role != User.Role.CUSTOMER:
        raise PermissionDenied
    cfg = settings_obj()
    profile = ensure_profile(request.user)
    balance = available_points(profile)
    referrals = profile.referrals.select_related("order").order_by("-created_at")[:20]
    ledger = profile.ledger_entries.select_related("referral", "redemption").order_by(
        "-created_at"
    )[:30]
    now = __import__("django.utils.timezone", fromlist=["timezone"]).now()
    next_expiry = (
        profile.point_batches.filter(remaining_points__gt=0, expires_at__gt=now)
        .order_by("expires_at")
        .first()
    )
    pending_points = sum(
        points_for_amount(r.eligible_amount, cfg)
        for r in profile.referrals.filter(
            status__in=[Referral.Status.PENDING, Referral.Status.MANUAL_REVIEW]
        )
    )
    used_points = abs(
        int(
            profile.ledger_entries.filter(kind=PointLedger.Kind.REDEEM).aggregate(
                v=Sum("points")
            )["v"]
            or 0
        )
    )
    expired_logged = abs(
        int(
            profile.ledger_entries.filter(kind=PointLedger.Kind.EXPIRE).aggregate(
                v=Sum("points")
            )["v"]
            or 0
        )
    )
    expired_unprocessed = int(
        profile.point_batches.filter(
            remaining_points__gt=0, expires_at__lte=now
        ).aggregate(v=Sum("remaining_points"))["v"]
        or 0
    )
    expired_points = expired_logged + expired_unprocessed
    return render(
        request,
        "ambassadors/account.html",
        {
            "program": cfg,
            "ambassador": profile,
            "balance": balance,
            "discount_value": discount_for_points(balance, cfg),
            "referrals": referrals,
            "ledger": ledger,
            "next_expiry": next_expiry,
            "successful_referrals": profile.referrals.filter(
                status=Referral.Status.AWARDED
            ).count(),
            "pending_referrals": profile.referrals.filter(
                status__in=[Referral.Status.PENDING, Referral.Status.MANUAL_REVIEW]
            ).count(),
            "pending_points": pending_points,
            "used_points": used_points,
            "expired_points": expired_points,
        },
    )


@require_POST
@login_required
def request_gift(request):
    if request.user.role != User.Role.CUSTOMER:
        raise PermissionDenied
    cfg = settings_obj()
    if not cfg.enabled:
        messages.error(request, "برنامج سفير هيبة السلطان متوقف حاليًا.")
        return redirect(AMBASSADOR_ACCOUNT_URL)
    profile = ensure_profile(request.user)
    balance = available_points(profile)
    if balance < cfg.redeem_points_block:
        messages.error(
            request,
            f"يلزم توفر {cfg.redeem_points_block} نقطة على الأقل لطلب الاستبدال.",
        )
        return redirect(AMBASSADOR_ACCOUNT_URL)
    if profile.redemptions.filter(
        kind=Redemption.Kind.GIFT, status=Redemption.Status.REQUESTED
    ).exists():
        messages.info(request, "لديك طلب هدية قيد المراجعة بالفعل.")
        return redirect(AMBASSADOR_ACCOUNT_URL)
    redemption = Redemption.objects.create(
        profile=profile,
        kind=Redemption.Kind.GIFT,
        points_used=0,
        amount_aed=0,
        status=Redemption.Status.REQUESTED,
        note="Customer requested available gift options",
    )
    audit(
        request,
        "ambassador_gift_requested",
        redemption,
        new={"ambassador_code": profile.code},
    )
    messages.success(
        request,
        "تم إرسال طلب الهدية للمتجر. لن تخصم أي نقاط حتى يتم الاتفاق على الهدية واعتمادها.",
    )
    return redirect(AMBASSADOR_ACCOUNT_URL)

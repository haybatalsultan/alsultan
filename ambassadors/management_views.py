from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.services.permission_service import can, require_owner
from core.management_views import _clean_search, _paginate, page_copy, staff_required
from core.services.audit_service import audit

from .models import (
    AmbassadorProfile,
    PointBatch,
    Redemption,
    Referral,
)
from .services.program import reconcile_referral, settings_obj


MANAGEMENT_AMBASSADORS_URL = 'core:management_ambassadors'

def _can_view(user):
    return user.role == User.Role.OWNER or can(user, "view_customers")


@staff_required
def dashboard(request):
    if not _can_view(request.user):
        raise PermissionDenied
    cfg = settings_obj()
    q = _clean_search(request)
    profiles = (
        AmbassadorProfile.objects.select_related("user")
        .annotate(
            referral_count=Count("referrals"),
            successful_count=Count(
                "referrals", filter=Q(referrals__status=Referral.Status.AWARDED)
            ),
            pending_count=Count(
                "referrals",
                filter=Q(
                    referrals__status__in=[
                        Referral.Status.PENDING,
                        Referral.Status.MANUAL_REVIEW,
                    ]
                ),
            ),
            referred_sales=Sum(
                "referrals__eligible_amount",
                filter=Q(referrals__status=Referral.Status.AWARDED),
            ),
            total_points=Sum(
                "referrals__points_awarded",
                filter=Q(referrals__status=Referral.Status.AWARDED),
            ),
        )
        .order_by("-successful_count", "-created_at")
    )
    if q:
        profiles = profiles.filter(
            Q(code__icontains=q)
            | Q(user__username__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(user__phone_e164__icontains=q)
            | Q(user__email__icontains=q)
            | Q(referrals__order__reference__icontains=q)
        ).distinct()
    page_obj, pagination_query = _paginate(request, profiles, 25)
    stats = {
        "registered": AmbassadorProfile.objects.count(),
        "active": AmbassadorProfile.objects.filter(
            referrals__status=Referral.Status.AWARDED
        )
        .distinct()
        .count(),
        "pending": Referral.objects.filter(
            status__in=[Referral.Status.PENDING, Referral.Status.MANUAL_REVIEW]
        ).count(),
        "manual_review": Referral.objects.filter(
            status=Referral.Status.MANUAL_REVIEW
        ).count(),
        "successful": Referral.objects.filter(status=Referral.Status.AWARDED).count(),
        "sales": Referral.objects.filter(status=Referral.Status.AWARDED).aggregate(
            v=Sum("eligible_amount")
        )["v"]
        or 0,
        "points": Referral.objects.filter(status=Referral.Status.AWARDED).aggregate(
            v=Sum("points_awarded")
        )["v"]
        or 0,
        "gift_requests": Redemption.objects.filter(
            kind=Redemption.Kind.GIFT, status=Redemption.Status.REQUESTED
        ).count(),
        "expiring_batches": PointBatch.objects.filter(remaining_points__gt=0).count(),
    }
    return render(
        request,
        "management/ambassadors/dashboard.html",
        {
            "program": cfg,
            "profiles": page_obj.object_list,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
            "q": q,
            "stats": stats,
            "is_owner": request.user.role == User.Role.OWNER,
            "recent_referrals": Referral.objects.select_related(
                "ambassador__user", "order"
            ).order_by("-created_at")[:12],
            "recent_gift_requests": Redemption.objects.filter(
                kind=Redemption.Kind.GIFT, status=Redemption.Status.REQUESTED
            )
            .select_related("profile__user")
            .order_by("-created_at")[:8],
            **page_copy(
                request,
                "إدارة سفراء هيبة السلطان",
                "Haybat Alsultan Ambassadors",
                "متابعة السفراء والإحالات والنقاط من صفحة واحدة واضحة.",
                "Monitor ambassadors, referrals and points from one clear page.",
            ),
        },
    )


@require_POST
@staff_required
def toggle(request):
    require_owner(request.user)
    cfg = settings_obj()
    old = cfg.enabled
    cfg.enabled = not cfg.enabled
    cfg.save(update_fields=["enabled", "updated_at"])
    audit(
        request,
        "ambassador_program_toggled",
        cfg,
        old={"enabled": old},
        new={"enabled": cfg.enabled},
    )
    messages.success(
        request,
        "تم تفعيل برنامج سفير هيبة السلطان."
        if cfg.enabled
        else "تم إيقاف برنامج سفير هيبة السلطان. البيانات والنقاط السابقة محفوظة.",
    )
    return redirect(MANAGEMENT_AMBASSADORS_URL)


@require_POST
@staff_required
@transaction.atomic
def review_referral(request, referral_id):
    """Owner-only resolution for guest referrals held from automatic payout."""
    require_owner(request.user)
    referral = (
        Referral.objects.select_for_update()
        .select_related("order", "ambassador__user")
        .filter(pk=referral_id)
        .first()
    )
    if not referral:
        raise PermissionDenied
    if referral.status != Referral.Status.MANUAL_REVIEW:
        messages.error(request, "هذه الإحالة ليست بانتظار المراجعة.")
        return redirect(MANAGEMENT_AMBASSADORS_URL)

    decision = (request.POST.get("decision") or "").strip().lower()
    if decision == "reject":
        referral.status = Referral.Status.REJECTED
        referral.review_reason = "OWNER_REJECTED"
        referral.reviewed_at = timezone.now()
        referral.save(update_fields=["status", "review_reason", "reviewed_at"])
        audit(
            request,
            "ambassador_referral_rejected",
            referral,
            old={"status": "REVIEW"},
            new={"status": "REJECTED"},
            metadata={"order": referral.order.reference},
        )
        messages.success(request, "تم رفض الإحالة بدون منح نقاط.")
        return redirect(MANAGEMENT_AMBASSADORS_URL)

    if decision != "approve":
        messages.error(request, "قرار المراجعة غير صالح.")
        return redirect(MANAGEMENT_AMBASSADORS_URL)

    order = referral.order
    if order.status != "DELIVERED" or order.payment_status != "PAID":
        messages.error(request, "لا يمكن اعتماد الإحالة قبل اكتمال الدفع والتسليم.")
        return redirect(MANAGEMENT_AMBASSADORS_URL)

    referral.status = Referral.Status.PENDING
    referral.review_reason = "OWNER_APPROVED"
    referral.reviewed_at = timezone.now()
    referral.save(update_fields=["status", "review_reason", "reviewed_at"])
    reconcile_referral(order, owner_approved=True)
    audit(
        request,
        "ambassador_referral_approved",
        referral,
        old={"status": "REVIEW"},
        new={"status": "AWARDED"},
        metadata={"order": order.reference},
    )
    messages.success(request, "تم اعتماد الإحالة ومنح النقاط المستحقة مرة واحدة فقط.")
    return redirect(MANAGEMENT_AMBASSADORS_URL)

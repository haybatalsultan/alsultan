from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from accounts.models import User
from orders.models import Order


@dataclass(frozen=True)
class RiskSignal:
    customer_id: str
    customer_name: str
    level: str
    code: str
    label_ar: str
    label_en: str
    evidence: str


def customer_risk_signals(*, days=30, limit=50):
    """Return review signals for the owner.

    These are deliberately conservative and informational. They never change a
    customer's account, order, loyalty tier, or access automatically.
    """
    since = timezone.now() - timedelta(days=max(1, min(int(days), 365)))
    customers = (
        User.objects.filter(role=User.Role.CUSTOMER)
        .annotate(
            recent_orders=Count(
                "orders", filter=Q(orders__created_at__gte=since), distinct=True
            ),
            recent_cancelled=Count(
                "orders",
                filter=Q(
                    orders__created_at__gte=since,
                    orders__status=Order.Status.CANCELLED,
                ),
                distinct=True,
            ),
            recent_returned=Count(
                "orders",
                filter=Q(
                    orders__created_at__gte=since,
                    orders__status=Order.Status.RETURNED,
                ),
                distinct=True,
            ),
            recent_failed_payments=Count(
                "orders",
                filter=Q(
                    orders__created_at__gte=since,
                    orders__payment_status=Order.PaymentStatus.FAILED,
                ),
                distinct=True,
            ),
        )
        .filter(
            Q(recent_cancelled__gte=3)
            | Q(recent_returned__gte=2)
            | Q(recent_failed_payments__gte=2)
            | Q(recent_orders__gte=6)
        )
        .only("public_id", "username", "first_name", "last_name")
        .order_by("-recent_cancelled", "-recent_returned", "-recent_failed_payments")[
            :limit
        ]
    )

    signals = []
    for user in customers:
        name = user.get_full_name() or user.username

        if user.recent_cancelled >= 3:
            ratio = (
                (user.recent_cancelled / user.recent_orders) * 100
                if user.recent_orders
                else 0
            )
            level = "HIGH" if ratio >= 70 and user.recent_orders >= 4 else "MEDIUM"
            signals.append(
                RiskSignal(
                    str(user.public_id),
                    name,
                    level,
                    "HIGH_CANCELLATION_RATE",
                    "إلغاءات متكررة تحتاج مراجعة",
                    "Repeated cancellations require review",
                    f"{user.recent_cancelled}/{user.recent_orders} cancelled in {days}d",
                )
            )

        if user.recent_returned >= 2:
            signals.append(
                RiskSignal(
                    str(user.public_id),
                    name,
                    "MEDIUM",
                    "REPEATED_RETURNS",
                    "مرتجعات متكررة",
                    "Repeated returns",
                    f"{user.recent_returned} returned orders in {days}d",
                )
            )

        if user.recent_failed_payments >= 2:
            signals.append(
                RiskSignal(
                    str(user.public_id),
                    name,
                    "MEDIUM",
                    "FAILED_PAYMENTS",
                    "محاولات دفع فاشلة متكررة",
                    "Repeated failed payments",
                    f"{user.recent_failed_payments} failed payments in {days}d",
                )
            )

        # Burst volume is only a review signal and does not imply fraud.
        if user.recent_orders >= 6:
            signals.append(
                RiskSignal(
                    str(user.public_id),
                    name,
                    "LOW",
                    "HIGH_ORDER_VELOCITY",
                    "نشاط طلبات مرتفع",
                    "High order activity",
                    f"{user.recent_orders} orders in {days}d",
                )
            )

    rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    signals.sort(key=lambda s: (rank.get(s.level, 9), s.customer_name))
    return signals[:limit]

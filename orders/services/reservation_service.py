import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from orders.models import Order, OrderTimelineEvent, PaymentAttempt, Reservation

from .inventory_service import release_order_reservations

logger = logging.getLogger("haybat.security")


def reservation_deadline(order):
    """Return the earliest active inventory reservation expiry for an order."""
    return (
        order.reservations.filter(released_at__isnull=True, consumed_at__isnull=True)
        .order_by("expires_at")
        .values_list("expires_at", flat=True)
        .first()
    )


def _stripe_client():
    if not getattr(settings, "STRIPE_ENABLED", False) or not getattr(
        settings, "STRIPE_SECRET_KEY", ""
    ):
        return None
    return stripe.StripeClient(settings.STRIPE_SECRET_KEY)


def _provider_safe_to_release(order_id):
    """Close open Stripe Checkout sessions before inventory is released.

    Returns True only when it is safe to release the local inventory hold.
    A provider outage or a payment that is already processing/paid is treated
    conservatively: inventory remains reserved and the cleanup job can retry.
    """
    now = timezone.now()
    attempts = list(
        PaymentAttempt.objects.filter(
            order_id=order_id,
            status__in=[
                PaymentAttempt.Status.CREATING,
                PaymentAttempt.Status.OPEN,
                PaymentAttempt.Status.PROCESSING,
            ],
        ).order_by("created_at")
    )
    if not attempts:
        return True

    client = _stripe_client()
    for attempt in attempts:
        # A provider-side processing state may already result in a captured
        # payment. Never free a unique item while that outcome is uncertain.
        if attempt.status == PaymentAttempt.Status.PROCESSING:
            return False

        if not attempt.checkout_session_id:
            # Allow a short in-flight create request to finish. A stale CREATING
            # marker can be failed locally because no customer-facing Stripe
            # session was persisted for it.
            if (now - attempt.created_at).total_seconds() < 120:
                return False
            PaymentAttempt.objects.filter(
                pk=attempt.pk, status=PaymentAttempt.Status.CREATING
            ).update(status=PaymentAttempt.Status.FAILED)
            continue

        if client is None:
            logger.warning(
                "reservation_expiry_stripe_unavailable order_id=%s attempt_id=%s",
                order_id,
                attempt.pk,
            )
            return False

        try:
            remote = client.v1.checkout.sessions.retrieve(attempt.checkout_session_id)
            remote_status = str(getattr(remote, "status", "") or "")
            remote_payment = str(getattr(remote, "payment_status", "") or "")

            if remote_status == "complete" or remote_payment == "paid":
                # Let webhook/reconciliation settle the already-completed payment.
                return False

            if remote_status == "open":
                remote = client.v1.checkout.sessions.expire(attempt.checkout_session_id)
                remote_status = str(getattr(remote, "status", "") or "")

            if remote_status != "expired":
                return False

            PaymentAttempt.objects.filter(
                pk=attempt.pk,
                status__in=[PaymentAttempt.Status.CREATING, PaymentAttempt.Status.OPEN],
            ).update(status=PaymentAttempt.Status.EXPIRED)
        except Exception:
            logger.exception(
                "reservation_expiry_provider_check_failed order_id=%s attempt_id=%s",
                order_id,
                attempt.pk,
            )
            return False
    return True


def expire_unpaid_order_if_needed(order_or_id):
    """Expire an unpaid 10-minute inventory hold without creating a payment race.

    Inventory is released only after any open Stripe Checkout session has been
    confirmed expired. Network/provider uncertainty keeps the inventory held and
    is retried by later page loads or the maintenance command.
    """
    order_id = getattr(order_or_id, "pk", order_or_id)

    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.payment_status == Order.PaymentStatus.PAID:
            return False
        if order.status in {
            Order.Status.CANCELLED,
            Order.Status.RETURNED,
            Order.Status.DELIVERED,
        }:
            return False
        active = list(
            Reservation.objects.select_for_update()
            .filter(order=order, released_at__isnull=True, consumed_at__isnull=True)
            .order_by("expires_at", "pk")
        )
        if not active or min(r.expires_at for r in active) > timezone.now():
            return False

    # Never perform a network call while holding the order/inventory DB locks.
    if not _provider_safe_to_release(order_id):
        return False

    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.payment_status == Order.PaymentStatus.PAID:
            return False
        if order.status in {
            Order.Status.CANCELLED,
            Order.Status.RETURNED,
            Order.Status.DELIVERED,
        }:
            return False
        active = list(
            Reservation.objects.select_for_update()
            .filter(order=order, released_at__isnull=True, consumed_at__isnull=True)
            .order_by("expires_at", "pk")
        )
        if not active or min(r.expires_at for r in active) > timezone.now():
            return False
        # Re-check provider markers after the external call. PROCESSING/OPEN means
        # another concurrent payment path won the race; keep inventory reserved.
        if (
            PaymentAttempt.objects.select_for_update()
            .filter(
                order=order,
                status__in=[
                    PaymentAttempt.Status.CREATING,
                    PaymentAttempt.Status.OPEN,
                    PaymentAttempt.Status.PROCESSING,
                ],
            )
            .exists()
        ):
            return False

        old_status = order.status
        old_payment = order.payment_status
        release_order_reservations(
            order, actor=None, reason="10-minute checkout reservation expired"
        )
        order.status = Order.Status.CANCELLED
        update_fields = ["status", "updated_at"]
        if order.payment_status == Order.PaymentStatus.PENDING:
            order.payment_status = Order.PaymentStatus.FAILED
            update_fields.append("payment_status")
        order.save(update_fields=update_fields)

        OrderTimelineEvent.objects.create(
            order=order,
            kind=OrderTimelineEvent.Kind.STATUS_CHANGED,
            label_ar="انتهت مهلة حجز الطلب وتم تحرير القطع",
            label_en="Checkout reservation expired and inventory was released",
            from_value=old_status,
            to_value=Order.Status.CANCELLED,
        )
        if old_payment != order.payment_status:
            OrderTimelineEvent.objects.create(
                order=order,
                kind=OrderTimelineEvent.Kind.PAYMENT_CHANGED,
                label_ar="انتهت مهلة الدفع قبل إتمام العملية",
                label_en="Payment window expired before completion",
                from_value=old_payment,
                to_value=order.payment_status,
            )
        return True


def release_expired(limit=500):
    """Retry expiry for abandoned unpaid orders in bounded batches."""
    ids = list(
        Reservation.objects.filter(
            released_at__isnull=True,
            consumed_at__isnull=True,
            expires_at__lte=timezone.now(),
            order__status=Order.Status.PENDING,
        )
        .order_by("expires_at")
        .values_list("order_id", flat=True)
        .distinct()[:limit]
    )
    count = 0
    for order_id in ids:
        if expire_unpaid_order_if_needed(order_id):
            count += 1
    return count

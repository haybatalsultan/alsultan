from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

import stripe
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from orders.models import Order, OrderTimelineEvent, PaymentAttempt, StripeWebhookEvent

from .inventory_service import consume_order_reservations, release_order_reservations
from .reservation_service import reservation_deadline

CHECKOUT_EXPIRED_MESSAGE = 'Checkout reservation expired.'

CENT = Decimal("0.01")


def _amount_minor(amount: Decimal) -> int:
    value = Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP)
    return int((value * 100).to_integral_value(rounding=ROUND_HALF_UP))


def _stripe_client():
    if not settings.STRIPE_ENABLED or not settings.STRIPE_SECRET_KEY:
        raise RuntimeError("Stripe payments are not configured.")
    return stripe.StripeClient(settings.STRIPE_SECRET_KEY)


def _assert_active_reservations(order: Order):
    """Validate that the checkout inventory hold is still active.

    Reservation.expires_at is immutable during customer payment-method changes.
    Provider-specific windows belong to PaymentAttempt.expires_at and must never
    silently extend the original checkout reservation.
    """
    now = timezone.now()
    reservations = list(
        order.reservations.select_for_update().select_related("product")
    )
    if not reservations:
        raise ValueError("Checkout reservation is missing.")
    for reservation in reservations:
        if reservation.released_at is not None or reservation.consumed_at is not None:
            raise ValueError("Checkout reservation is no longer active.")
        if reservation.expires_at <= now:
            raise ValueError(CHECKOUT_EXPIRED_MESSAGE)
    return reservations


def _release_reservations(order: Order, reason: str):
    return release_order_reservations(order, actor=None, reason=reason)


def create_checkout_session(*, order: Order, request):
    if order.payment_status == Order.PaymentStatus.PAID:
        raise ValueError("Order is already paid.")
    if order.status in {Order.Status.CANCELLED, Order.Status.RETURNED}:
        raise ValueError("Order cannot be paid in its current state.")

    now = timezone.now()
    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        if (
            locked.payment_method == Order.PaymentMethod.MANUAL
            and locked.payment_status == Order.PaymentStatus.PAID
        ):
            raise ValueError("Order was completed using manual payment.")
        deadline = reservation_deadline(locked)
        if not deadline or deadline <= now:
            raise ValueError(CHECKOUT_EXPIRED_MESSAGE)
        active = (
            locked.payment_attempts.select_for_update()
            .filter(
                status__in=[
                    PaymentAttempt.Status.CREATING,
                    PaymentAttempt.Status.OPEN,
                    PaymentAttempt.Status.PROCESSING,
                ]
            )
            .order_by("-created_at")
            .first()
        )
        if (
            active
            and active.checkout_session_id
            and active.expires_at
            and active.expires_at > now
        ):
            try:
                remote = _stripe_client().v1.checkout.sessions.retrieve(
                    active.checkout_session_id
                )
                if getattr(remote, "status", None) == "open" and getattr(
                    remote, "url", None
                ):
                    return remote
            except stripe.StripeError:
                pass
            active.status = PaymentAttempt.Status.FAILED
            active.save(update_fields=["status", "updated_at"])
        elif (
            active
            and active.status == PaymentAttempt.Status.CREATING
            and (now - active.created_at).total_seconds() < 90
        ):
            raise ValueError(
                "A payment session is already being created. Please try again shortly."
            )

        minutes = max(30, min(int(settings.STRIPE_CHECKOUT_MINUTES), 1440))
        expires_at = now + timezone.timedelta(minutes=minutes)
        _assert_active_reservations(locked)
        attempt = PaymentAttempt.objects.create(
            order=locked,
            attempt_key=uuid4(),
            status=PaymentAttempt.Status.CREATING,
            amount=locked.grand_total,
            currency=locked.currency.upper(),
            expires_at=expires_at,
        )

    success_url = request.build_absolute_uri(
        reverse("orders:payment_success", kwargs={"public_id": order.public_id})
    )
    cancel_url = (
        request.build_absolute_uri(
            reverse("orders:confirmation", kwargs={"public_id": order.public_id})
        )
        + "?payment=cancelled"
    )
    params = {
        "mode": "payment",
        "client_reference_id": order.reference,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "expires_at": int(expires_at.timestamp()),
        "line_items": [
            {
                "quantity": 1,
                "price_data": {
                    "currency": order.currency.lower(),
                    "unit_amount": _amount_minor(order.grand_total),
                    "product_data": {
                        "name": f"Haybat Al Sultan — {order.reference}",
                        "description": f"{order.items.count()} item(s)",
                    },
                },
            }
        ],
        "metadata": {
            "order_public_id": str(order.public_id),
            "order_reference": order.reference,
            "payment_attempt": str(attempt.attempt_key),
        },
    }
    if order.customer_email:
        params["customer_email"] = order.customer_email

    try:
        session = _stripe_client().v1.checkout.sessions.create(
            params,
            options={"idempotency_key": f"haybat-checkout-{attempt.attempt_key}"},
        )
    except Exception:
        PaymentAttempt.objects.filter(pk=attempt.pk).update(
            status=PaymentAttempt.Status.FAILED
        )
        raise

    with transaction.atomic():
        attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        attempt.checkout_session_id = session.id
        attempt.status = PaymentAttempt.Status.OPEN
        attempt.save(update_fields=["checkout_session_id", "status", "updated_at"])
        locked = Order.objects.select_for_update().get(pk=order.pk)
        current_deadline = reservation_deadline(locked)
        reservation_expired_during_provider_create = bool(
            not current_deadline or current_deadline <= timezone.now()
        )
        method_changed = locked.payment_method != Order.PaymentMethod.STRIPE
        if method_changed:
            locked.payment_method = Order.PaymentMethod.STRIPE
        if locked.payment_status in {
            Order.PaymentStatus.UNPAID,
            Order.PaymentStatus.FAILED,
        }:
            old = locked.payment_status
            locked.payment_status = Order.PaymentStatus.PENDING
            fields = ["payment_status", "updated_at"]
            if method_changed:
                fields.append("payment_method")
            locked.save(update_fields=fields)
            OrderTimelineEvent.objects.create(
                order=locked,
                kind=OrderTimelineEvent.Kind.PAYMENT_CHANGED,
                label_ar="تم بدء عملية الدفع الآمن",
                label_en="Secure payment started",
                from_value=old,
                to_value=Order.PaymentStatus.PENDING,
            )
        elif method_changed:
            locked.save(update_fields=["payment_method", "updated_at"])

    if reservation_expired_during_provider_create:
        # The customer crossed the local inventory deadline while Stripe was
        # creating the provider session. Persist the session first, then use the
        # central expiry routine to close Stripe before inventory can be released.
        from .reservation_service import expire_unpaid_order_if_needed

        expire_unpaid_order_if_needed(order.pk)
        raise ValueError(CHECKOUT_EXPIRED_MESSAGE)
    return session


def _order_from_session_object(obj):
    session_id = obj.get("id", "")
    attempt = (
        PaymentAttempt.objects.select_for_update()
        .select_related("order")
        .filter(checkout_session_id=session_id)
        .first()
    )
    if not attempt:
        raise ValueError("Unknown Stripe Checkout Session.")
    metadata = obj.get("metadata") or {}
    if (
        metadata.get("order_public_id") != str(attempt.order.public_id)
        or metadata.get("order_reference") != attempt.order.reference
    ):
        raise ValueError("Stripe metadata mismatch.")
    if (obj.get("currency") or "").upper() != attempt.currency.upper():
        raise ValueError("Stripe currency mismatch.")
    if int(obj.get("amount_total") or -1) != _amount_minor(attempt.amount):
        raise ValueError("Stripe amount mismatch.")
    return attempt


def _mark_paid(attempt: PaymentAttempt, obj):
    order = Order.objects.select_for_update().get(pk=attempt.order_id)
    if order.payment_status == Order.PaymentStatus.REFUNDED:
        return
    attempt.payment_intent_id = str(
        obj.get("payment_intent") or attempt.payment_intent_id or ""
    )[:255]
    attempt.status = PaymentAttempt.Status.PAID
    attempt.paid_at = attempt.paid_at or timezone.now()
    attempt.save(update_fields=["payment_intent_id", "status", "paid_at", "updated_at"])

    old_payment = order.payment_status
    old_status = order.status
    changed = []
    if order.payment_method != Order.PaymentMethod.STRIPE:
        order.payment_method = Order.PaymentMethod.STRIPE
        changed.append("payment_method")
    if order.payment_status != Order.PaymentStatus.PAID:
        order.payment_status = Order.PaymentStatus.PAID
        changed.append("payment_status")
    if order.status == Order.Status.PENDING:
        order.status = Order.Status.CONFIRMED
        changed.append("status")
    if changed:
        changed.append("updated_at")
        order.save(update_fields=changed)

    consume_order_reservations(order, order.user)
    if old_payment != order.payment_status:
        OrderTimelineEvent.objects.create(
            order=order,
            kind=OrderTimelineEvent.Kind.PAYMENT_CHANGED,
            label_ar="تم استلام الدفعة عبر Stripe",
            label_en="Stripe payment received",
            from_value=old_payment,
            to_value=order.payment_status,
        )
    if old_status != order.status:
        OrderTimelineEvent.objects.create(
            order=order,
            kind=OrderTimelineEvent.Kind.STATUS_CHANGED,
            label_ar="تم تأكيد الطلب بعد نجاح الدفع",
            label_en="Order confirmed after successful payment",
            from_value=old_status,
            to_value=order.status,
        )
    if (
        old_payment != Order.PaymentStatus.PAID
        and order.payment_status == Order.PaymentStatus.PAID
    ):
        transaction.on_commit(
            lambda order_id=order.pk: __import__(
                "orders.services.notification_service",
                fromlist=["notify_payment_received"],
            ).notify_payment_received(order_id),
            robust=True,
        )


def _mark_failed(attempt: PaymentAttempt, *, expired=False):
    order = Order.objects.select_for_update().get(pk=attempt.order_id)
    if order.payment_status == Order.PaymentStatus.PAID:
        return
    attempt.status = (
        PaymentAttempt.Status.EXPIRED if expired else PaymentAttempt.Status.FAILED
    )
    attempt.save(update_fields=["status", "updated_at"])
    old = order.payment_status
    order.payment_status = Order.PaymentStatus.FAILED
    order.save(update_fields=["payment_status", "updated_at"])
    _release_reservations(
        order, "Stripe Checkout expired" if expired else "Stripe payment failed"
    )
    if old != order.payment_status:
        OrderTimelineEvent.objects.create(
            order=order,
            kind=OrderTimelineEvent.Kind.PAYMENT_CHANGED,
            label_ar="انتهت جلسة الدفع" if expired else "تعذر إتمام الدفع",
            label_en="Payment session expired" if expired else "Payment failed",
            from_value=old,
            to_value=order.payment_status,
        )


def _handle_refund(charge):
    payment_intent = str(charge.get("payment_intent") or "")
    if not payment_intent:
        return
    attempt = (
        PaymentAttempt.objects.select_for_update()
        .select_related("order")
        .filter(payment_intent_id=payment_intent)
        .order_by("-created_at")
        .first()
    )
    if not attempt:
        return
    order = Order.objects.select_for_update().get(pk=attempt.order_id)
    if (charge.get("currency") or "").upper() != order.currency.upper():
        raise ValueError("Refund currency mismatch.")
    refunded_minor = int(charge.get("amount_refunded") or 0)
    full = refunded_minor >= _amount_minor(order.grand_total)
    new_payment = Order.PaymentStatus.REFUNDED if full else Order.PaymentStatus.PARTIAL
    old = order.payment_status
    if old != new_payment:
        order.payment_status = new_payment
        order.save(update_fields=["payment_status", "updated_at"])
        attempt.status = (
            PaymentAttempt.Status.REFUNDED if full else PaymentAttempt.Status.PARTIAL
        )
        attempt.save(update_fields=["status", "updated_at"])
        OrderTimelineEvent.objects.create(
            order=order,
            kind=OrderTimelineEvent.Kind.PAYMENT_CHANGED,
            label_ar="تم تسجيل استرجاع دفعة Stripe",
            label_en="Stripe refund recorded",
            from_value=old,
            to_value=new_payment,
        )


def _stripe_field(obj, key, default=None):
    """Read one field from either a plain dict or stripe-python StripeObject.

    StripeObject is intentionally not treated as a normal Mapping here: current
    stripe-python releases do not expose dict.get consistently.  Reading only
    the allow-listed fields also avoids copying provider payloads into the
    payment domain unnecessarily.
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    try:
        return obj[key]
    except (KeyError, TypeError, IndexError):
        return getattr(obj, key, default)


def _plain_checkout_session(session):
    metadata = _stripe_field(session, "metadata", None)
    return {
        "id": str(_stripe_field(session, "id", "") or ""),
        "currency": str(_stripe_field(session, "currency", "") or ""),
        "amount_total": _stripe_field(session, "amount_total", None),
        "payment_status": str(_stripe_field(session, "payment_status", "") or ""),
        "status": str(_stripe_field(session, "status", "") or ""),
        "payment_intent": _stripe_field(session, "payment_intent", ""),
        "metadata": {
            "order_public_id": str(
                _stripe_field(metadata, "order_public_id", "") or ""
            ),
            "order_reference": str(
                _stripe_field(metadata, "order_reference", "") or ""
            ),
        },
    }


def _retrieve_checkout_session(session_id: str):
    """Retrieve a Checkout Session server-to-server using the configured test/live key.

    This mirrors the retrieval path verified during sandbox diagnosis and keeps
    reconciliation independent from StripeClient response-wrapper differences.
    """
    if not settings.STRIPE_ENABLED or not settings.STRIPE_SECRET_KEY:
        raise RuntimeError("Stripe payments are not configured.")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe.checkout.Session.retrieve(session_id)


def reconcile_payment_attempt(attempt: PaymentAttempt) -> str:
    """Verify one recorded Checkout Session against Stripe and safely converge local state.

    This is a server-to-server fallback for delayed/missed webhooks. It never trusts
    browser query parameters and reuses the same amount/currency/metadata validation
    as webhook processing.
    """
    if not attempt.checkout_session_id:
        return "no_session"
    if (
        attempt.status == PaymentAttempt.Status.PAID
        and attempt.order.payment_status == Order.PaymentStatus.PAID
    ):
        return "paid"

    remote = _retrieve_checkout_session(attempt.checkout_session_id)
    obj = _plain_checkout_session(remote)

    with transaction.atomic():
        validated = _order_from_session_object(obj)
        if validated.pk != attempt.pk:
            raise ValueError("Stripe payment attempt mismatch.")
        remote_status = str(obj.get("status") or "")
        remote_payment = str(obj.get("payment_status") or "")
        if remote_status == "complete" and remote_payment == "paid":
            _mark_paid(validated, obj)
            return "paid"
        if remote_status == "expired":
            _mark_failed(validated, expired=True)
            return "expired"
        if remote_status == "complete" and remote_payment and remote_payment != "paid":
            validated.status = PaymentAttempt.Status.PROCESSING
            validated.save(update_fields=["status", "updated_at"])
            return "processing"
        return remote_status or remote_payment or "unchanged"


def reconcile_order_payment(order: Order) -> str:
    if order.payment_status == Order.PaymentStatus.PAID:
        return "paid"
    attempt = (
        order.payment_attempts.exclude(checkout_session_id__isnull=True)
        .exclude(checkout_session_id="")
        .filter(
            status__in=[
                PaymentAttempt.Status.OPEN,
                PaymentAttempt.Status.PROCESSING,
                PaymentAttempt.Status.PAID,
            ]
        )
        .order_by("-created_at")
        .first()
    )
    if not attempt:
        return "no_attempt"
    return reconcile_payment_attempt(attempt)


def process_webhook_event(event):
    event_id = str(event.get("id") or "")
    event_type = str(event.get("type") or "")
    if not event_id or not event_type:
        raise ValueError("Invalid Stripe event.")

    with transaction.atomic():
        if StripeWebhookEvent.objects.filter(event_id=event_id).exists():
            return False
        obj = event["data"]["object"]
        if event_type in {
            "checkout.session.completed",
            "checkout.session.async_payment_succeeded",
        }:
            attempt = _order_from_session_object(obj)
            attempt.payment_intent_id = str(
                obj.get("payment_intent") or attempt.payment_intent_id or ""
            )[:255]
            if obj.get("payment_status") == "paid" or event_type.endswith(
                "async_payment_succeeded"
            ):
                _mark_paid(attempt, obj)
            else:
                attempt.status = PaymentAttempt.Status.PROCESSING
                attempt.save(
                    update_fields=["payment_intent_id", "status", "updated_at"]
                )
        elif event_type == "checkout.session.async_payment_failed":
            attempt = _order_from_session_object(obj)
            _mark_failed(attempt)
        elif event_type == "checkout.session.expired":
            attempt = _order_from_session_object(obj)
            _mark_failed(attempt, expired=True)
        elif event_type == "charge.refunded":
            _handle_refund(obj)
        StripeWebhookEvent.objects.create(event_id=event_id, event_type=event_type)
    return True

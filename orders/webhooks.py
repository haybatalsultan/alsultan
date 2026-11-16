import logging

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services.stripe_service import process_webhook_event

logger = logging.getLogger("haybat.security")


def _normalise_stripe_event(event):
    """Return a plain Python structure after Stripe has verified the signature.

    stripe-python returns an Event/StripeObject.  The payment domain deliberately
    works with ordinary dict/list values so it does not depend on SDK object
    semantics (StripeObject does not provide dict.get in current SDK versions).
    """
    to_dict_recursive = getattr(event, "to_dict_recursive", None)
    if callable(to_dict_recursive):
        return to_dict_recursive()
    if isinstance(event, dict):
        return event
    raise ValueError("Unsupported Stripe event payload type.")


@csrf_exempt  # NOSONAR -- Stripe authenticates requests with Stripe-Signature.
@require_POST
def stripe_webhook(request):
    """Stripe-only CSRF exemption; authenticity is enforced by Stripe-Signature."""
    if not settings.STRIPE_ENABLED or not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse(status=503)
    signature = request.headers.get("Stripe-Signature", "")
    if not signature:
        return HttpResponse(status=400)
    try:
        event = stripe.Webhook.construct_event(
            payload=request.body,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
        process_webhook_event(_normalise_stripe_event(event))
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)
    except Exception as exc:
        # Never log the request body, Stripe-Signature, API keys, or webhook secret.
        # The exception class/message plus traceback are enough to diagnose the
        # integration while keeping payment/security material out of logs.
        logger.exception(
            "stripe_webhook_processing_failed exception_type=%s",
            type(exc).__name__,
        )
        # A non-2xx response tells Stripe to retry. Never acknowledge a
        # provider event whose database transaction did not complete.
        return HttpResponse(status=500)
    return HttpResponse(status=200)

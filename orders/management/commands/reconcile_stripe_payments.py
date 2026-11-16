from django.core.management.base import BaseCommand, CommandError

from orders.models import Order, PaymentAttempt
from orders.services.stripe_service import reconcile_payment_attempt


class Command(BaseCommand):
    help = "Reconcile locally pending Stripe Checkout attempts against Stripe server-side state."

    def add_arguments(self, parser):
        parser.add_argument(
            "--order",
            dest="order_reference",
            help="Reconcile one order reference only.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum attempts to inspect (1-500).",
        )

    def handle(self, *args, **options):
        limit = max(1, min(int(options["limit"]), 500))
        qs = (
            PaymentAttempt.objects.select_related("order")
            .exclude(checkout_session_id__isnull=True)
            .exclude(checkout_session_id="")
            .filter(
                status__in=[
                    PaymentAttempt.Status.OPEN,
                    PaymentAttempt.Status.PROCESSING,
                ]
            )
            .order_by("created_at")
        )
        reference = (options.get("order_reference") or "").strip().upper()
        if reference:
            if not Order.objects.filter(reference=reference).exists():
                raise CommandError("Order reference was not found.")
            qs = qs.filter(order__reference=reference)

        checked = paid = expired = unchanged = errors = 0
        for attempt in qs[:limit]:
            checked += 1
            try:
                result = reconcile_payment_attempt(attempt)
            except (
                Exception
            ) as exc:  # Command output must not expose provider payloads or secrets.
                errors += 1
                self.stderr.write(
                    f"{attempt.order.reference}: reconciliation failed ({type(exc).__name__})"
                )
                continue
            if result == "paid":
                paid += 1
            elif result == "expired":
                expired += 1
            else:
                unchanged += 1
            self.stdout.write(f"{attempt.order.reference}: {result}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Checked={checked} paid={paid} expired={expired} unchanged={unchanged} errors={errors}"
            )
        )

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from orders.models import Order
from orders.services.inventory_service import consume_order_reservations


class Command(BaseCommand):
    help = "Audit paid orders whose inventory reservations were not converted to sales."

    def add_arguments(self, parser):
        parser.add_argument("--order", dest="reference")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply safe reservation-to-sale conversions.",
        )

    def handle(self, *args, **options):
        qs = Order.objects.filter(payment_status=Order.PaymentStatus.PAID).order_by(
            "id"
        )
        if options["reference"]:
            qs = qs.filter(reference=options["reference"])
            if not qs.exists():
                raise CommandError("Order not found.")
        checked = pending = fixed = errors = 0
        for order in qs:
            active = order.reservations.filter(consumed_at__isnull=True)
            if not active.exists():
                continue
            checked += 1
            pending += 1
            released = active.filter(released_at__isnull=False).exists()
            if released:
                errors += 1
                self.stderr.write(
                    f"{order.reference}: MANUAL REVIEW (reservation already released)"
                )
                continue
            if not options["apply"]:
                self.stdout.write(f"{order.reference}: needs inventory conversion")
                continue
            try:
                with transaction.atomic():
                    locked = Order.objects.select_for_update().get(pk=order.pk)
                    consume_order_reservations(locked)
                fixed += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{order.reference}: inventory converted to sale"
                    )
                )
            except Exception as exc:
                errors += 1
                self.stderr.write(f"{order.reference}: failed ({type(exc).__name__})")
        self.stdout.write(
            f"checked={checked} pending={pending} fixed={fixed} errors={errors} apply={options['apply']}"
        )

from django.core.management.base import BaseCommand

from orders.services.cart_service import purge_expired_cart_items


class Command(BaseCommand):
    help = (
        "Release expired cart inventory reservations and remove the expired cart items."
    )

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=500)

    def handle(self, *args, **options):
        count = purge_expired_cart_items(limit=options["limit"])
        self.stdout.write(self.style.SUCCESS(f"released={count}"))

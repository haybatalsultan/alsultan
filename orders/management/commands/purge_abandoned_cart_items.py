from django.core.management.base import BaseCommand

from orders.services.cart_service import purge_abandoned_cart_items


class Command(BaseCommand):
    help = "Delete informational cart items older than CART_ITEM_RETENTION_DAYS (default 30)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=1000)

    def handle(self, *args, **options):
        limit = max(1, min(int(options["limit"]), 10000))
        total = purge_abandoned_cart_items(limit=limit)
        self.stdout.write(self.style.SUCCESS(f"deleted={total}"))

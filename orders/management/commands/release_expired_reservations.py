from django.core.management.base import BaseCommand

from orders.services.reservation_service import release_expired


class Command(BaseCommand):
    help = "Release expired pending reservations safely."

    def handle(self, *args, **opts):
        self.stdout.write(
            self.style.SUCCESS(f"Released {release_expired()} reservations.")
        )

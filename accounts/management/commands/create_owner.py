import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = "Create the single protected owner account interactively."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--email", required=True)

    def handle(self, *args, **options):
        if User.objects.filter(role=User.Role.OWNER).exists():
            raise CommandError("An owner account already exists.")

        user = User(
            username=options["username"],
            email=options["email"].strip().lower(),
            role=User.Role.OWNER,
            is_staff=False,
            is_superuser=False,
            is_active=True,
        )
        password = getpass.getpass("Owner password: ")
        try:
            validate_password(password, user=user)
            user.full_clean(exclude=("password",))
        except ValidationError as exc:
            raise CommandError(
                "Owner credentials are invalid: " + "; ".join(exc.messages)
            ) from exc

        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS("Protected owner created."))

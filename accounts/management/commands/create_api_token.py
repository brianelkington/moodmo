from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.models import ApiToken


class Command(BaseCommand):
    help = "Create an API token for a user."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            required=True,
            help="Email address of the user who will own the token.",
        )
        parser.add_argument(
            "--name",
            default="",
            help="Optional label for the token.",
        )

    def handle(self, *args, **options):
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=options["email"])
        except user_model.DoesNotExist as exc:
            raise CommandError(f"No user found with email {options['email']!r}.") from exc

        _, raw_key = ApiToken.create_for_user(user, name=options["name"])
        self.stdout.write(self.style.SUCCESS("API token created."))
        self.stdout.write(raw_key)
        self.stdout.write(
            "Store this token securely; it will not be shown again."
        )

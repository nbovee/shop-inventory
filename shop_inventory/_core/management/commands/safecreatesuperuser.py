"""
This custom management command creates a superuser if it doesn't exist.
Does not have interactive handling like createsuperuser.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = "Safely create an admin user if there are no users, and quietly exit if it already exists."

    def add_arguments(self, parser):
        parser.add_argument("--username", help="Username for superuser")
        parser.add_argument("--email", help="Email for superuser")
        parser.add_argument("--password", help="Password for superuser")
        parser.add_argument(
            "--no-input",
            "--noinput",
            help="Use preset options from within the environment",
            action="store_true",
        )
        parser.add_argument(
            "--populated",
            help="Attempt creation even if the user table is populated",
            action="store_true",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.exists():
            self.stderr.write(self.style.WARNING("User table already exists."))
            if not options["populated"]:
                return
        if options["no_input"]:
            options["username"] = os.environ["DJANGO_SUPERUSER_USERNAME"]
            options["email"] = os.environ["DJANGO_SUPERUSER_EMAIL"]
            options["password"] = os.environ["DJANGO_SUPERUSER_PASSWORD"]

        defaults = {
            "email": options["email"],
            "password": make_password(options["password"]),
            "is_superuser": True,
            "is_staff": True,
        }

        obj, created = User.objects.get_or_create(
            username=options["username"],
            defaults=defaults,
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Superuser created: {obj}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superuser already exists: {obj}"))

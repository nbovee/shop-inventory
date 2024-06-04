import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = "Loads all fixture files"

    def handle(self, *args, **options):
        # Get the current directory
        project_dir = os.path.dirname(settings.BASE_DIR)

        # Find all fixture files in the project directory
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.endswith(".json") and "fixture" in root:
                    self.stdout.write(f"Loading fixture {file}")
                    call_command("loaddata", file)

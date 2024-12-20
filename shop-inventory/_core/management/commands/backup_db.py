from django.core.management.base import BaseCommand
import os
import zipfile
import glob
from datetime import datetime
import shutil


class Command(BaseCommand):
    help = "Create encrypted backup of the database on mounted backup drives"

    def find_backup_drives(self):
        """Find all mounted drives with a .shopbackup file"""
        # Common mount points for USB drives on Linux
        mount_points = ["/media", "/mnt"]
        backup_drives = []

        for mount_point in mount_points:
            if os.path.exists(mount_point):
                # Walk through all subdirectories
                for root, dirs, files in os.walk(mount_point):
                    if ".shopbackup" in files:
                        backup_drives.append(root)

        return backup_drives

    def handle(self, *args, **options):
        """Create a password-protected zip backup of the database"""
        from django.conf import settings

        db_path = settings.DATABASES["default"]["NAME"]
        backup_password = os.environ.get("BACKUP_PASSWORD")

        if not backup_password:
            self.stderr.write("Error: BACKUP_PASSWORD environment variable not set")
            return

        # Create timestamp for backup file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"shop_backup_{timestamp}.zip"

        # Find drives to backup to
        backup_drives = self.find_backup_drives()

        if not backup_drives:
            self.stderr.write("No backup drives found with .shopbackup file")
            return

        # Create a temporary copy of the database
        temp_db = f"/tmp/db_backup_{timestamp}.sqlite3"
        shutil.copy2(db_path, temp_db)

        try:
            # Create encrypted zip file
            for drive in backup_drives:
                zip_path = os.path.join(drive, zip_filename)

                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.setpassword(backup_password.encode())
                    zf.write(temp_db, "database.sqlite3")

                self.stdout.write(self.style.SUCCESS(f"Backup created at: {zip_path}"))

                # Keep only the 5 most recent backups
                existing_backups = sorted(
                    glob.glob(os.path.join(drive, "shop_backup_*.zip"))
                )
                if len(existing_backups) > 5:
                    for old_backup in existing_backups[:-5]:
                        os.remove(old_backup)
                        self.stdout.write(
                            self.style.SUCCESS(f"Removed old backup: {old_backup}")
                        )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_db):
                os.remove(temp_db)

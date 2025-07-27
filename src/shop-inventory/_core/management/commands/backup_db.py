from django.core.management.base import BaseCommand
import os
import pyzipper
import glob
from datetime import datetime
import shutil
import logging

# Set up logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create encrypted backup of the database on mounted backup drives"

    def find_backup_drives(self):
        """Find all mounted drives with a .shopbackup file"""
        # Common mount points for USB drives on Linux
        mount_points = ["/tmp/shop-backup-mounts"]
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
        backup_password = os.environ.get("DJANGO_BACKUP_PASSWORD")

        if not backup_password:
            logger.error("DJANGO_BACKUP_PASSWORD environment variable not set")
            return

        # Create timestamp for backup file
        timestamp = datetime.now().strftime("%Y-%m-%d")
        zip_filename = f"shop_backup_{timestamp}.zip"

        # Find drives to backup to
        backup_drives = self.find_backup_drives()

        if not backup_drives:
            logger.error("No backup drives found with .shopbackup file")
            return

        # Create a temporary copy of the database
        temp_db = f"/tmp/db_backup_{timestamp}.sqlite3"
        shutil.copy2(db_path, temp_db)

        try:
            # Create encrypted zip file with AES encryption
            for drive in backup_drives:
                zip_path = os.path.join(drive, zip_filename)

                # Use AESZipFile instead of ZipFile for better encryption
                with pyzipper.AESZipFile(
                    zip_path,
                    "w",
                    compression=pyzipper.ZIP_LZMA,
                    encryption=pyzipper.WZ_AES,
                ) as zf:
                    zf.setpassword(backup_password.encode())
                    zf.write(temp_db, arcname="db.sqlite3")

                logger.info(f"Backup created at: {zip_path}")

                # Keep only the 5 most recent backups
                existing_backups = sorted(
                    glob.glob(os.path.join(drive, "shop_backup_*.zip"))
                )
                if len(existing_backups) > 100:
                    for old_backup in existing_backups[:-100]:
                        os.remove(old_backup)
                        logger.info(f"Removed old backup: {old_backup}")

        finally:
            # Clean up temporary file
            if os.path.exists(temp_db):
                os.remove(temp_db)

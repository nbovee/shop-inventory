#!/usr/bin/env python3
import os
import sys
import zipfile
import glob
from datetime import datetime
from pathlib import Path
import shutil

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent.parent / "shop-inventory"
sys.path.append(str(project_dir))

# Import Django settings to get DATABASE path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_core.settings")
from django.conf import settings  # noqa: E402


def find_backup_drives():
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


def create_backup():
    """Create a password-protected zip backup of the database"""
    db_path = settings.DATABASES["default"]["NAME"]
    backup_password = os.environ.get("BACKUP_PASSWORD")

    if not backup_password:
        print("Error: BACKUP_PASSWORD environment variable not set")
        sys.exit(1)

    # Create timestamp for backup file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"shop_backup_{timestamp}.zip"

    # Find drives to backup to
    backup_drives = find_backup_drives()

    if not backup_drives:
        print("No backup drives found with .shopbackup file")
        sys.exit(1)

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

            print(f"Backup created at: {zip_path}")

            # Keep only the 5 most recent backups
            existing_backups = sorted(
                glob.glob(os.path.join(drive, "shop_backup_*.zip"))
            )
            if len(existing_backups) > 5:
                for old_backup in existing_backups[:-5]:
                    os.remove(old_backup)
                    print(f"Removed old backup: {old_backup}")

    finally:
        # Clean up temporary file
        if os.path.exists(temp_db):
            os.remove(temp_db)


if __name__ == "__main__":
    create_backup()

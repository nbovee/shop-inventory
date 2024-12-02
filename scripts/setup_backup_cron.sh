#!/bin/bash

# Make backup script executable
chmod +x "$(dirname "$0")/backup_db.py"

# Get the absolute path to backup_db.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_db.py"

# Check if BACKUP_PASSWORD is set in environment
if [ -z "$BACKUP_PASSWORD" ]; then
    echo "Error: BACKUP_PASSWORD environment variable is not set"
    echo "Please set it first: export BACKUP_PASSWORD='your_password'"
    exit 1
fi

# Create the cron job line
# Note: The cron job will inherit BACKUP_PASSWORD from the environment
CRON_LINE="0 * * * * $BACKUP_SCRIPT"

# Check if the cron job already exists
if crontab -l 2>/dev/null | grep -Fq "$BACKUP_SCRIPT"; then
    echo "Backup cron job already exists"
else
    # Add new cron job while preserving existing ones
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "Added backup cron job successfully"
fi

echo "To verify your crontab, run: crontab -l"

#!/bin/bash
set -e

# Load environment variables
# service should already have sourced the config file but some of the chaining seems to fail
source /etc/shop-inventory/config

# Activate virtual environment
source "${APP_INSTALL_DIR}/venv/bin/activate"

echo "Confirming python & gunicorn are in the virtual environment"
which python
which gunicorn

echo "Collecting static files"
python manage.py collectstatic --noinput

echo "Migrating database"
python manage.py migrate --noinput

# Start Gunicorn
exec gunicorn _core.wsgi:application \
    --name shop_inventory \
    --bind unix:"${APP_RUN_DIR}/shop-inventory.sock" \
    --log-file "${APP_LOG_DIR}/gunicorn.log" \
    --access-logfile "${APP_LOG_DIR}/gunicorn-access.log" \
    --error-logfile "${APP_LOG_DIR}/gunicorn-error.log" \
    --capture-output \
    --pid "${APP_RUN_DIR}/gunicorn.pid" \
    --workers "${GUNICORN_WORKERS}" \
    --timeout "${GUNICORN_TIMEOUT}" \
    --log-level "${GUNICORN_LOG_LEVEL}" \
    --max-requests "${GUNICORN_MAX_REQUESTS}" \
    --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER}"

#!/bin/bash
set -e

# Load environment variables
. .env

# Activate virtual environment
source venv/bin/activate

# Start Gunicorn
exec gunicorn _core.wsgi:application \
    --name shop_inventory \
    --bind unix:run/shop-inventory.sock \
    --log-file logs/gunicorn.log \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --capture-output \
    --pid run/gunicorn.pid \
    --workers "${SHOP_GUNICORN_WORKERS}" \
    --timeout "${SHOP_GUNICORN_TIMEOUT}" \
    --log-level "${SHOP_GUNICORN_LOG_LEVEL}" \
    --max-requests "${SHOP_GUNICORN_MAX_REQUESTS}" \
    --max-requests-jitter "${SHOP_GUNICORN_MAX_REQUESTS_JITTER}"

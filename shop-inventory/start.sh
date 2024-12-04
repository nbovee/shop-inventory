#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Ensure required directories exist
mkdir -p logs
mkdir -p run

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn _core.wsgi:application \
    --name shop_inventory \
    --workers 3 \
    --bind unix:run/shop-inventory.sock \
    --log-level info \
    --log-file logs/gunicorn.log \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --capture-output \
    --pid run/gunicorn.pid \
    --timeout 120
    --max-requests 1000
    --max-requests-jitter 50

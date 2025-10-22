#!/bin/sh
# vim:sw=4:ts=4:et

# Load environment variables from config file if it exists
if [ -f /etc/pantry/config ]; then
  set -a
  . /etc/pantry/config
  set +a
fi

su-exec "$USER" python manage.py collectstatic --noinput
su-exec "$USER" python manage.py migrate --noinput

if [ "$1" = "--debug" ]; then
  # Django development server
  exec su-exec "$USER" python manage.py runserver "0.0.0.0:$DJANGO_DEV_SERVER_PORT"

else
  # Gunicorn
  exec su-exec "$USER" python manage.py migrate --noinput
  exec su-exec "$USER" gunicorn "_core.wsgi:application" \
    --bind "0.0.0.0:$GUNICORN_PORT" \
    --workers "$GUNICORN_WORKERS" \
    --timeout "$GUNICORN_TIMEOUT" \
    --log-level "$GUNICORN_LOG_LEVEL" \
    --max-requests "$GUNICORN_MAX_REQUESTS" \
    --max-requests-jitter "$GUNICORN_MAX_REQUESTS_JITTER"
fi

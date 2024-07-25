#!/bin/sh
# vim:sw=4:ts=4:et

su-exec "$USER" python manage.py collectstatic --noinput

# Creating the first user in the system
# USER_EXISTS="from django.contrib.auth import get_user_model; User = get_user_model(); exit(User.objects.exists())"
# su-exec "$USER" python manage.py shell -c "$USER_EXISTS" && su-exec "$USER" python manage.py createsuperuser --noinput

if [ "$1" = "--debug" ]; then
  # Django development server
  exec su-exec "$USER" python manage.py runserver "0.0.0.0:$DJANGO_DEV_SERVER_PORT"
  # these should run somewhere around here instead of from dockerfile
  # python manage.py makemigrations && \
	# python manage.py migrate && \
	# python manage.py loaddata core/fixtures/users.json && \
	# python manage.py loaddata core/fixtures/orders.json && \
	# python manage.py loaddata core/fixtures/locations.json && \
	# python manage.py loaddata core/fixtures/inventory.json
else
  # Gunicorn
  exec su-exec "$USER" gunicorn "$PROJECT_NAME.wsgi:application" \
    --bind "0.0.0.0:$GUNICORN_PORT" \
    --workers "$GUNICORN_WORKERS" \
    --timeout "$GUNICORN_TIMEOUT" \
    --log-level "$GUNICORN_LOG_LEVEL"
fi

#!/bin/bash -e

. "${BASE_DIR}/config"
on_chroot << EOF
# Collect static files
cd "${APP_INSTALL_DIR}"
# activate venv
source "${APP_INSTALL_DIR}/venv/bin/activate"
which python
echo "Collecting static files"
python manage.py collectstatic --noinput

echo "Migrating database"
python manage.py migrate --noinput

echo "Creating first superuser"
python manage.py safecreatesuperuser --noinput

EOF

#!/bin/bash -e

. "${BASE_DIR}/config"
on_chroot << EOF
echo "Running commands as ${APP_USER} to test the build"
cd "${APP_INSTALL_DIR}"

# Run commands as APP_USER (without changing directory)
su "${APP_USER}" << 'USEREOF'
# activate venv
source "${APP_INSTALL_DIR}/venv/bin/activate"
echo "Confirming python & gunicorn are in the virtual environment"
which python
which gunicorn
echo "Collecting static files"
python manage.py collectstatic --noinput

echo "Migrating database"
python manage.py migrate --noinput

USEREOF

EOF

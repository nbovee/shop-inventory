#!/bin/bash -e

. "${BASE_DIR}/config"
on_chroot << EOF
# Collect static files
cd "${SHOP_INSTALL_DIR}"
# activate venv
source "${SHOP_INSTALL_DIR}/venv/bin/activate"
which python
echo "Collecting static files"
python3 manage.py collectstatic --noinput

echo "Migrating database"
python3 manage.py migrate --noinput

echo "Creating first superuser"
python3 manage.py createsuperuser --noinput

EOF

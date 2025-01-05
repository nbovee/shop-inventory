#!/bin/bash -e

. "${BASE_DIR}/config"
on_chroot << EOF
# Collect static files
cd "${SHOP_INSTALL_DIR}"
"${SHOP_INSTALL_DIR}/venv/bin/python" manage.py collectstatic --noinput

# Create initial database
"${SHOP_INSTALL_DIR}/venv/bin/python" manage.py migrate --noinput

# Create superuser
"${SHOP_INSTALL_DIR}/venv/bin/python" manage.py createsuperuser --noinput

EOF

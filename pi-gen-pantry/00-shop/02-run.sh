#!/bin/bash -e

# Export environment variables for chroot
export SHOP_INSTALL_DIR
export SHOP_DJANGO_SUPERUSER_USERNAME SHOP_DJANGO_SUPERUSER_PASSWORD SHOP_DJANGO_SUPERUSER_EMAIL

on_chroot << EOF
# Collect static files
cd ${SHOP_INSTALL_DIR}
${SHOP_INSTALL_DIR}/venv/bin/python manage.py collectstatic --noinput

# Create initial database
${SHOP_INSTALL_DIR}/venv/bin/python manage.py migrate --noinput

# Create superuser
${SHOP_INSTALL_DIR}/venv/bin/python manage.py createsuperuser --noinput

# Enable services to start on boot
systemctl enable nginx
EOF

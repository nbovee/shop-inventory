#!/bin/bash -e

# Export environment variables for chroot
export SHOP_HOSTNAME=${SHOP_HOSTNAME}
export SHOP_INSTALL_DIR=${SHOP_INSTALL_DIR}
export SHOP_DJANGO_SQLITE_DIR=${SHOP_DJANGO_SQLITE_DIR}
export SHOP_DJANGO_STATIC_ROOT=${SHOP_DJANGO_STATIC_ROOT}

# Configure WiFi hotspot
on_chroot << EOF
# Configure hostname
echo "${SHOP_HOSTNAME}" > /etc/hostname
sed -i "s/127.0.1.1.*/127.0.1.1\t${SHOP_HOSTNAME}/" /etc/hosts

# Create required directories
mkdir -p "${SHOP_INSTALL_DIR}"
mkdir -p "${SHOP_DJANGO_SQLITE_DIR}"
mkdir -p "${SHOP_INSTALL_DIR}/logs"
mkdir -p "${SHOP_INSTALL_DIR}/run"
mkdir -p "${SHOP_DJANGO_STATIC_ROOT}"

# Set up Python virtual environment
python3 -m venv "${SHOP_INSTALL_DIR}/venv"
"${SHOP_INSTALL_DIR}/venv/bin/pip" install --upgrade pip
"${SHOP_INSTALL_DIR}/venv/bin/pip" install -r /tmp/files/requirements.txt

# Copy project files from the files directory
cp -r /tmp/files/* "${SHOP_INSTALL_DIR}/"

# Set up permissions
chown -R www-data:www-data "${SHOP_INSTALL_DIR}"
chown -R www-data:www-data "${SHOP_DJANGO_SQLITE_DIR}"
chmod +x "${SHOP_INSTALL_DIR}/start.sh"

# Set up cron job for backups
PYTHON_PATH="${SHOP_INSTALL_DIR}/venv/bin/python"
MANAGE_PY="${SHOP_INSTALL_DIR}/manage.py"
echo "0 * * * * cd ${SHOP_INSTALL_DIR} && \${PYTHON_PATH} \${MANAGE_PY} backup_db" | crontab -u www-data -

# Install and enable services
cp /tmp/files/shop-inventory.service /etc/systemd/system/
systemctl enable shop-inventory

# Configure nginx
cp /tmp/files/nginx-shop-inventory.conf /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/nginx-shop-inventory.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
EOF

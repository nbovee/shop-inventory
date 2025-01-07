#!/bin/bash -e

. "${BASE_DIR}/config"
on_chroot << EOF
echo "Configure hostname"
echo "${SHOP_HOSTNAME}" > /etc/hostname
sed -i "s/127.0.1.1.*/127.0.1.1\t${SHOP_HOSTNAME}/" /etc/hosts

echo "Create required directories"
echo "SHOP_INSTALL_DIR: ${SHOP_INSTALL_DIR}"
mkdir -p "${SHOP_INSTALL_DIR}"
mkdir -p "${DJANGO_SQLITE_DIR}"
mkdir -p "${SHOP_INSTALL_DIR}/logs"
mkdir -p "${SHOP_INSTALL_DIR}/run"
mkdir -p "${DJANGO_STATIC_ROOT}"
ls "${SHOP_INSTALL_DIR}"
EOF

echo "Copy project files from the files directory"
pwd
# sleep 10000
# somehow we are losing the ROOTFS_DIR variable, so atm we just hardcode it
# /pi-gen/work/rowanPantry/rootfs/
cp -r files/shop-inventory "/pi-gen/work/rowanPantry/pi-gen-pantry/rootfs${SHOP_INSTALL_DIR}"
install -m 644 files/requirements.txt "/pi-gen/work/rowanPantry/pi-gen-pantry/rootfs${SHOP_INSTALL_DIR}"
install -m 644 files/shop-inventory.service "/pi-gen/work/rowanPantry/pi-gen-pantry/rootfs/etc/systemd/system/"
install -m 644 files/nginx-shop-inventory.conf "/pi-gen/work/rowanPantry/pi-gen-pantry/rootfs/etc/nginx/sites-available/"
install -m 644 files/shop-wifi-setup.service "/pi-gen/work/rowanPantry/pi-gen-pantry/rootfs/etc/systemd/system/"

on_chroot << EOF
echo "Set up permissions"
chown -R www-data:www-data "${SHOP_INSTALL_DIR}"
chown -R www-data:www-data "${DJANGO_SQLITE_DIR}"
chmod +x "${SHOP_INSTALL_DIR}/start.sh"

echo "Set up Python virtual environment"
python3 -m venv "${SHOP_INSTALL_DIR}/venv"
"${SHOP_INSTALL_DIR}/venv/bin/pip" install --upgrade pip
"${SHOP_INSTALL_DIR}/venv/bin/pip" install -r "${SHOP_INSTALL_DIR}/requirements.txt"

echo "Set up cron job for backups"
PYTHON_PATH="${SHOP_INSTALL_DIR}/venv/bin/python"
MANAGE_PY="${SHOP_INSTALL_DIR}/manage.py"
echo "0 * * * * cd ${SHOP_INSTALL_DIR} && \${PYTHON_PATH} \${MANAGE_PY} backup_db" | crontab -u www-data -

echo "Configure nginx"
ln -sf /etc/nginx/sites-available/nginx-shop-inventory.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
EOF

#!/bin/bash -e

. "${BASE_DIR}/config"

on_chroot << EOF
echo " adding user:"${APP_USER}" to group:"${APP_GROUP}""
usermod -aG "${APP_GROUP}" "${APP_USER}"
echo "add user:root to the group:"${APP_GROUP}""
usermod -aG ${APP_GROUP} root

echo "Configure hostname"
echo "${TARGET_HOSTNAME}" > /etc/hostname
sed -i "s/127.0.1.1.*/127.0.1.1\t${TARGET_HOSTNAME}/" /etc/hosts

echo "Create required directories"
mkdir -p "${APP_INSTALL_DIR}"
mkdir -p "${APP_INSTALL_DIR}/${DJANGO_SQLITE_DIR}"
mkdir -p "${APP_INSTALL_DIR}/${DJANGO_STATIC_ROOT}"
mkdir -p "${APP_ENV_DIR}"
mkdir -p "${APP_LOG_DIR}"
mkdir -p "${APP_RUN_DIR}"
EOF

echo "Copy project files from the files directory"
# /pi-gen/work/rowanPantry/rootfs/
cp -r files/shop-inventory/* "${ROOTFS_DIR}${APP_INSTALL_DIR}"
install -m 640 files/requirements.txt "${ROOTFS_DIR}${APP_INSTALL_DIR}"
echo "Copying systemd service & configuration files"
install -m 640 files/shop-inventory.service "${ROOTFS_DIR}/etc/systemd/system/"
install -m 640 files/nginx-shop-inventory.conf "${ROOTFS_DIR}/etc/nginx/sites-available/"
install -m 640 files/shop-wifi-setup.service "${ROOTFS_DIR}/etc/systemd/system/"
install -m 640 files/shop-inventory-socket.conf "${ROOTFS_DIR}/usr/lib/tmpfiles.d/"
install -m 640 files/shop-inventory-logs.conf "${ROOTFS_DIR}/usr/lib/tmpfiles.d/"
install -m 640 files/dnsmasq.conf "${ROOTFS_DIR}/etc/dnsmasq.conf"

echo "Copying config file"
install -m 640 "${BASE_DIR}/config" "${ROOTFS_DIR}/etc/shop-inventory/config"

on_chroot << EOF
chown -R root:${APP_GROUP} "${APP_ENV_DIR}"

echo "Set up Python virtual environment"
python3 -m venv "${APP_INSTALL_DIR}/venv"
"${APP_INSTALL_DIR}/venv/bin/pip" install --upgrade pip
"${APP_INSTALL_DIR}/venv/bin/pip" install -r "${APP_INSTALL_DIR}/requirements.txt"

echo "Set up permissions"
chown -R ${APP_USER}:${APP_GROUP} "${APP_INSTALL_DIR}"
chown -R ${APP_USER}:${APP_GROUP} "${APP_LOG_DIR}"
chown -R ${APP_USER}:${APP_GROUP} "${APP_RUN_DIR}"
chmod +x "${APP_INSTALL_DIR}/start.sh"
chmod +x "${APP_INSTALL_DIR}/manage.py"

echo "Set up cron job for backups"
echo "0 * * * * ${APP_INSTALL_DIR}/venv/bin/python ${APP_INSTALL_DIR}/manage.py backup_db >> ${APP_LOG_DIR}/backup.log 2>&1" | crontab -u ${APP_USER} -

echo "Configure nginx"
ln -sf /etc/nginx/sites-available/nginx-shop-inventory.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
EOF

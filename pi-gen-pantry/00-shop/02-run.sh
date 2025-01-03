#!/bin/bash -e

on_chroot << EOF
# Collect static files
cd /opt/shop-inventory
/opt/shop-inventory/venv/bin/python manage.py collectstatic --noinput

# Create initial database
cd /opt/shop-inventory
/opt/shop-inventory/venv/bin/python manage.py migrate --noinput

# Enable services to start on boot
systemctl enable nginx
systemctl enable shop-inventory

# Create a first-boot service to generate a new secret key
cat > /etc/systemd/system/shop-inventory-firstboot.service << 'EOL'
[Unit]
Description=First boot configuration for Shop Inventory
Before=shop-inventory.service
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'SECRET_KEY=$(openssl rand -base64 32) && sed -i "s/default-key-change-on-first-boot/$SECRET_KEY/" /opt/shop-inventory/.env'
RemainAfter=no

[Install]
WantedBy=multi-user.target
EOL

# Enable first boot service
systemctl enable shop-inventory-firstboot
EOF

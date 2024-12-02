#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

echo "Installing system dependencies..."
apt-get update
apt-get install -y python3-pip python3-venv nginx

echo "Setting up directory structure..."
mkdir -p /opt/shop-inventory
mkdir -p /var/lib/shop-inventory
mkdir -p /opt/shop-inventory/logs
mkdir -p /opt/shop-inventory/run

echo "Copying project files..."
cp -r "$SCRIPT_DIR"/* /opt/shop-inventory/

echo "Setting up Python virtual environment..."
python3 -m venv /opt/shop-inventory/venv
source /opt/shop-inventory/venv/bin/activate

# Install both requirements files
echo "Installing Python dependencies..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

echo "Setting correct permissions..."
chown -R www-data:www-data /opt/shop-inventory
chown -R www-data:www-data /var/lib/shop-inventory
chmod +x /opt/shop-inventory/scripts/start.sh

echo "Installing systemd service..."
cp "$SCRIPT_DIR/scripts/shop-inventory.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable shop-inventory

echo "Configuring nginx..."
cp "$SCRIPT_DIR/scripts/nginx-shop-inventory.conf" /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/nginx-shop-inventory.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo "Creating .env file template..."
cat > /opt/shop-inventory/.env.template << 'EOL'
# Django settings
DJANGO_SECRET_KEY=change-me-to-a-real-secret-key
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=your-domain.com,another-domain.com
DJANGO_SQLITE_DIR=/var/lib/shop-inventory
DJANGO_STATIC_ROOT=/opt/shop-inventory/static

# Backup settings
BACKUP_PASSWORD=change-me-to-a-secure-password
EOL

echo "Starting services..."
systemctl start shop-inventory
systemctl restart nginx

echo "Installation complete!"
echo
echo "Next steps:"
echo "1. Copy /opt/shop-inventory/.env.template to /opt/shop-inventory/.env"
echo "2. Edit /opt/shop-inventory/.env with your settings"
echo "3. Restart the service: systemctl restart shop-inventory"
echo
echo "To check status:"
echo "  systemctl status shop-inventory"
echo "  journalctl -u shop-inventory"
echo "  tail -f /opt/shop-inventory/logs/gunicorn.log"
echo
echo "To check nginx:"
echo "  systemctl status nginx"
echo "  tail -f /var/log/nginx/shop-inventory-error.log"
echo
echo "Your site should now be accessible at http://your-server-ip/"

# Check if services are running
if ! systemctl is-active --quiet shop-inventory; then
    echo
    echo "WARNING: shop-inventory service is not running!"
    echo "Check the logs with: journalctl -u shop-inventory"
fi

if ! systemctl is-active --quiet nginx; then
    echo
    echo "WARNING: nginx service is not running!"
    echo "Check the logs with: journalctl -u nginx"
fi

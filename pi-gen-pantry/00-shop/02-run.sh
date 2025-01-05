#!/bin/bash -e

. "${BASE_DIR}/config"
on_chroot << EOF
# Create first-boot service for WiFi configuration
cat > /etc/systemd/system/shop-wifi-setup.service << 'EOL'
[Unit]
Description=Shop WiFi Hotspot Setup
After=network.target NetworkManager.service
Before=shop-inventory.service

[Service]
Type=oneshot
Environment=SHOP_WIFI_SSID=${SHOP_WIFI_SSID}
Environment=SHOP_WIFI_PASSWORD=${SHOP_WIFI_PASSWORD}
ExecStart=/bin/bash -c '\
    nmcli connection add type wifi ifname wlan0 con-name "$SHOP_WIFI_SSID" autoconnect yes ssid "$SHOP_WIFI_SSID" -- \
    wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$SHOP_WIFI_PASSWORD" \
    ipv4.method shared && \
    nmcli connection modify "$SHOP_WIFI_SSID" connection.autoconnect yes connection.autoconnect-priority 100'
RemainAfter=no

[Install]
WantedBy=multi-user.target
EOL

# Enable the WiFi setup service
systemctl enable shop-wifi-setup
EOF

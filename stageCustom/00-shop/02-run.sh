#!/bin/bash -e

. "${BASE_DIR}/config"

on_chroot << EOF
echo "Enable services to start on boot"
systemctl enable shop-wifi-setup
systemctl enable shop-inventory
systemctl enable shop-backup.timer
systemctl enable nginx
systemctl enable dnsmasq

EOF

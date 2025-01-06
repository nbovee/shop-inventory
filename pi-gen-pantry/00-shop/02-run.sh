#!/bin/bash -e

. "${BASE_DIR}/config"

on_chroot << EOF
echo "Enable services to start on boot"
systemctl enable nginx
systemctl enable shop-inventory
systemctl enable shop-wifi-setup
EOF

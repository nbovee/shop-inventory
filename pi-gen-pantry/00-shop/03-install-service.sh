install -m 644 files/shop-inventory.service "${ROOTFS_DIR}/lib/systemd/system/"

on_chroot << EOF
systemctl enable shop-inventory
EOF

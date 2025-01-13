#!/usr/bin/env bash

## Initialize git submodules if needed
git submodule update --init

## disable export for standard stages
touch ./pi-gen/stage2/SKIP_IMAGES ./pi-gen/stage2/SKIP_NOOBS
touch ./pi-gen/stage4/SKIP_IMAGES ./pi-gen/stage4/SKIP_NOOBS
touch ./pi-gen/stage5/SKIP_IMAGES ./pi-gen/stage5/SKIP_NOOBS

## link config
ln -s ../config ./pi-gen

## link custom stage and shop-inventory
ln -s ../stageCustom ./pi-gen/
mkdir -p ./pi-gen/stageCustom/00-shop/files
ln -s ../src/shop-inventory ./stageCustom/00-shop/files/

## link build directory
mkdir -p ./pi-gen/deploy
ln -s ./pi-gen/deploy .

## Create config if it doesn't exist
if [[ ! -f config ]]; then
    echo "Creating initial config file..."
    cp config.example config
    echo "Please configure the following in config:"
    echo "- DJANGO_SECRET_KEY: Django's secret key"
    echo "- DJANGO_DEBUG: Development mode (true/false)"
    echo "- WIFI_PASS: WiFi hotspot password"
    echo "- DJANGO_SUPERUSER_PASSWORD: Admin password"
    echo "- DJANGO_BACKUP_PASSWORD: Backup encryption password"
fi

## Set up ARM emulation for WSL if needed
if grep -q microsoft /proc/version; then
    echo "WSL detected, setting up ARM emulation..."
    sudo apt-get update
    sudo apt-get install -y qemu-user-static
    sudo update-binfmts --enable
fi
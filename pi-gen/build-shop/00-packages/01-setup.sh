#!/bin/bash -e





#!/bin/bash
# This script configures and starts a WiFi hotspot using NetworkManager
#
# It performs the following:
# 1. Creates a WiFi hotspot with specified SSID and password using wlan0 interface
# 2. Enables autoconnect for the hotspot connection with high priority
#
# Required environment variables:
# - HOTSPOT_SSID: Name of the WiFi network to create
# - HOTSPOT_PASSWORD: Password for the WiFi network

sudo nmcli device wifi hotspot ssid "${HOTSPOT_SSID}" password "${HOTSPOT_PASSWORD}" ifname wlan0

sudo nmcli connection modify id "${HOTSPOT_SSID}" connection.autoconnect yes connection.autoconnect-priority 100

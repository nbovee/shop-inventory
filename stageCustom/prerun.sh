#!/bin/bash -e

# borrowed from pi-gen existing stages

# This script runs before the stage's packages are installed
# The -e flag makes the script exit immediately if any command fails

# Check if the root filesystem directory exists
# ROOTFS_DIR is an environment variable set by pi-gen containing the path to the root filesystem
if [ ! -d "${ROOTFS_DIR}" ]; then
	# If the directory doesn't exist, copy the root filesystem from the previous stage
	# copy_previous is a pi-gen function that copies the filesystem from the last completed stage
	copy_previous
fi

#!/bin/sh
# Docker entrypoint script
set -e

# Execute the command passed to the container
exec "$@"

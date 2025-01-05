#!/usr/bin/env bash

# shellcheck disable=SC2164
if docker ps -a --format '{{.Names}}' | grep -q '^pigen_work'; then
    echo "Existing pigen_work container found - running Docker build with CONTINUE=1"
    (cd ./pi-gen; CONTINUE=1 ./build-docker.sh)
else
    echo "Running fresh Docker build"
    (cd ./pi-gen; ./build-docker.sh)
fi

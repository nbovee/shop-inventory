#!/usr/bin/env bash

## disable export for stage2
touch ./pi-gen/stage2/SKIP_IMAGES ./pi-gen/stage2/SKIP_NOOBS

## link config
ln -s ../config ./pi-gen

## link build directory
[[ ! -d ./pi-gen/deploy ]] && mkdir ./pi-gen/deploy
ln -s ./pi-gen/deploy .

#!/usr/bin/env bash

## disable export for stage2
touch ./pi-gen/stage2/SKIP_IMAGES ./pi-gen/stage2/SKIP_NOOBS

## link config
ln -s ../config ./pi-gen

## link shop-inventory to pi-gen-pantry/00-shop/files
ln -s ../shop-inventory ./pi-gen-pantry/00-shop/files

## link build directory
[[ ! -d ./pi-gen/deploy ]] && mkdir ./pi-gen/deploy
ln -s ./pi-gen/deploy .

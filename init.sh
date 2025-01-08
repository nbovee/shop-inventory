#!/usr/bin/env bash

## disable export for stage2
touch ./pi-gen/stage2/SKIP_IMAGES ./pi-gen/stage2/SKIP_NOOBS

## disable export for stage4
touch ./pi-gen/stage4/SKIP_IMAGES ./pi-gen/stage4/SKIP_NOOBS

## disable export for stage5
touch ./pi-gen/stage5/SKIP_IMAGES ./pi-gen/stage5/SKIP_NOOBS

## link config
ln -s ../config ./pi-gen

## link build directory
[[ ! -d ./pi-gen/deploy ]] && mkdir ./pi-gen/deploy
ln -s ./pi-gen/deploy .

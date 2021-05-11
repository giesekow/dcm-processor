#!/bin/bash
set -o allexport; source .env; set +o allexport

[ -z "$BASEDIR" ] && echo "set BASEDIR variable in the .env file" && exit 1
[ -z "$MODULES" ] && echo "set MODULES variable in the .env file" && exit 1
[ -z "$REGISTRY" ] && echo "set REGISTRY variable in the .env file" && exit 1
[ -z "$DATA" ] && echo "set DATA variable in the .env file" && exit 1
[ -z "$LOGS" ] && echo "set  variable in the .env file" && exit 1

mkdir -p "$BASEDIR/$MODULES"
mkdir -p "$BASEDIR/$REGISTRY"
mkdir -p "$BASEDIR/$DATA"
mkdir -p "$BASEDIR/$LOGS"
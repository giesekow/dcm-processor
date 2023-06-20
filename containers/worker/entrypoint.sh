#!/bin/bash

export TZ=Europe/Berlin
export DEBIAN_FRONTEND=noninteractive
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
export DISPLAY=:0

WLOGS="$LOGS/worker.txt"

python start.py

ENVARGS=$(python envs.py)

unset HTTP_PROXY
unset http_proxy

unset HTTPS_PROXY
unset https_proxy

python-mqas worker $ENVARGS --modules="$MODULES" --conn="$JOBS_CONNECTION" --dbname="$JOBS_DBNAME" --colname="$JOBS_COLNAME" --log-file="$WLOGS"
#!/bin/bash

export TZ=Europe/Berlin
export DEBIAN_FRONTEND=noninteractive
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
export DISPLAY=:0

REQUIREMENTS="$MODULES/*/requirements.txt"
SLOGS="$LOGS/shell.txt"
PLOGS="$LOGS/pip.txt"
SCRIPTS="$MODULES/*/script.sh"

alias pip='python -m pip'

for SCRIPT in $(ls $SCRIPTS)
do
  bash "$SCRIPT"
done

for REQUIREMENT in $(ls $REQUIREMENTS)
do
  python -m pip install -r "$REQUIREMENT" --trusted-host=pypi.python.org --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --default-timeout=100
done

watchmedo shell-command -w -p="$REQUIREMENTS" -R -D -c ' requirements.sh "${watch_event_type} ${watch_src_path}" >> $PLOGS ' &

watchmedo shell-command -w -p="$SCRIPTS" -R -D -c ' script.sh "${watch_event_type} ${watch_src_path}" >> $SLOGS ' &

rq worker --path "$MODULES" -u "redis://:$REDIS_PSWD@$REDIS_HOST:$REDIS_PORT"  $JOBS
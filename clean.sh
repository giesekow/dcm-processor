#!/bin/bash

docker-compose down

SCRIPT=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT")

readarray -d / -t strarr <<< "$BASEDIR"
for (( n=0; n < ${#strarr[*]}; n++))
do
  BASE="${strarr[n]}"
done

docker rmi "${BASE}_dashboard"
docker rmi "${BASE}_scheduler"
docker rmi "${BASE}_worker"

docker volume rm "${BASE}_redis-data"
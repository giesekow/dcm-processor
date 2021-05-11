#!/bin/bash

docker-compose down

SCRIPT=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT")

for i in $(echo $BASEDIR | tr "/" "\n")
do
  BASE="${i}"  
done

docker rmi "${BASE}_dashboard"
docker rmi "${BASE}_scheduler"
docker rmi "${BASE}_worker"

docker volume rm "${BASE}_redis-data"
#!/bin/bash

docker-compose stop $1
docker-compose rm $1


SCRIPT=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT")

for i in $(echo $BASEDIR | tr "/" "\n")
do
  BASE="${i}"  
done

docker rmi "${BASE}_$1"

docker-compose build $1

docker-compose up -d $1
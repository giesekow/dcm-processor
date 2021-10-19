#!/bin/bash

repo=giesekow/dcm-processor
tag=0.0.1

if [ -z $2 ]
then
  echo "tag not provided using $tag"
else
  tag=$2
fi

if [ $1 = "build" ]
then
  #filter="${repo}-*:${tag}"
  #docker rmi -f $(docker images --filter=reference="$filter" -q)
  #docker build -f ./Dockerfile-orthanc -t ${repo}-orthanc:${tag} ../
  docker build -f ./Dockerfile-worker -t ${repo}-worker:${tag} ../
  #docker build -f ./Dockerfile-scheduler -t ${repo}-scheduler:${tag} ../
fi

if [ $1 = "clean" ]
then
  filter="${repo}-*:${tag}"
  docker rmi -f $(docker images --filter=reference="$filter" -q)
fi

if [ $1 = "push" ]
then
  docker login
  #docker push ${repo}-orthanc:${tag}
  docker push ${repo}-worker:${tag}
  #docker push ${repo}-scheduler:${tag}
fi
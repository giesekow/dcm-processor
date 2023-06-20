#!/bin/bash

repo=giesekow/dcm-processor
tag=0.0.2

if [ -z $2 ]
then
  echo "tag not provided using $tag"
else
  tag=$2
fi

if [ $1 = "build" ]
then
  filter="${repo}-*:${tag}"
  #docker rmi -f $(docker images --filter=reference="$filter" -q)
  docker build -f ./Dockerfile-orthanc -t ${repo}-orthanc:${tag} ../containers/orthanc
  #docker build -f ./Dockerfile-worker -t ${repo}-worker:${tag} ../containers/worker
  #docker build -f ./Dockerfile-scheduler -t ${repo}-scheduler:${tag} ../containers/scheduler
fi

if [ $1 = "clean" ]
then
  filter="${repo}-*:${tag}"
  docker rmi -f $(docker images --filter=reference="$filter" -q)
fi

if [ $1 = "push" ]
then
  docker login
  docker push ${repo}-orthanc:${tag}
  #docker push ${repo}-worker:${tag}
  #docker push ${repo}-scheduler:${tag}
fi

if [ $1 = "pack" ]
then
  mkdir -p images
  rm -rf images/*
  docker save ${repo}-orthanc:${tag} | gzip > images/orthanc.tar.gz
  #docker save ${repo}-worker:${tag} | gzip > images/worker.tar.gz
  #docker save ${repo}-scheduler:${tag} | gzip > images/scheduler.tar.gz
fi
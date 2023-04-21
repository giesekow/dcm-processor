#!/bin/bash

export DISPLAY=:0

apt-get update
apt-get install -y wkhtmltopdf cmake
apt-get install -y openjdk-8-jdk default-jre git
#!/bin/bash

export DISPLAY=:0

apt-get update
apt-get install -y wkhtmltopdf cmake
apt-get install -y openjdk-8-jdk default-jre git

#  install niftyreg
git clone git://git.code.sf.net/p/niftyreg/git /niftyreg-git

mkdir /niftyreg-build
mkdir /niftyreg-install

curwd=${pwd}

cd /niftyreg-build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/niftyreg-install ${curwd}/niftyreg-git
make && make install

cd $curwd
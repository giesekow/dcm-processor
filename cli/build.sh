#!/bin/bash

rm -rf build
rm -rf dist
rm -rf *.egg-info
#python3 -m build
python3 setup.py sdist
python3 setup.py bdist_wheel
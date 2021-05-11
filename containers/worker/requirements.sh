#!/bin/bash

if [ $1 = "closed" ]
then
  python -m pip install -r "$2" --trusted-host=pypi.python.org --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --default-timeout=100
fi

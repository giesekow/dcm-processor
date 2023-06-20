#!/bin/bash

export PYTHONPATH="${PYTHONPATH}:${REGISTRY}"

unset HTTP_PROXY
unset http_proxy

unset HTTPS_PROXY
unset https_proxy

python-mqas init --conn $JOBS_CONNECTION --dbname $JOBS_DBNAME --colname $JOBS_COLNAME

flask run --host=0.0.0.0
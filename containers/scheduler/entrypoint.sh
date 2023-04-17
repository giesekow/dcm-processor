#!/bin/bash

export PYTHONPATH="${PYTHONPATH}:${REGISTRY}"

python-mqas init --conn $JOBS_CONNECTION --dbname $JOBS_DBNAME --colname $JOBS_COLNAME

flask run --host=0.0.0.0
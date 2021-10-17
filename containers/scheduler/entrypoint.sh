#!/bin/bash

export PYTHONPATH="${PYTHONPATH}:${REGISTRY}"

flask run --host=0.0.0.0
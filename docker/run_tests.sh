#!/bin/bash

cd /swaggerit
pip install -r requirements-dev.txt -r requirements.txt
py.test -c pytest-docker.ini $@

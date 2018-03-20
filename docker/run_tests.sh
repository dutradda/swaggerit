#!/bin/bash

export LANG=C.UTF-8
cd /swaggerit
tox -c tox-docker.ini

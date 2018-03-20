FROM ubuntu:16.04

MAINTAINER Diogo Dutra <dutradda@gmail.com>

RUN set -x \
 && apt-get update -qq \
 && DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
        software-properties-common \
 && add-apt-repository -y ppa:deadsnakes/ppa \
 && apt-get update -qq \
 && DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
        python3.5-dev \
        python3.6-dev \
        git \
        apt-transport-https \
        ca-certificates \
        curl \
        build-essential \
 && rm -rf /var/lib/apt/lists/* \
 && curl -SsL 'https://bootstrap.pypa.io/get-pip.py' | python3 \
 && pip install tox

ENV TOXENV ''
ADD run_tests.sh /usr/bin/run-tests
CMD ["run-tests"]

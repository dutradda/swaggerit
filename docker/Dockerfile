FROM python:3.6-alpine

MAINTAINER Diogo Dutra <dutradda@gmail.com>
RUN apk update && apk add bash alpine-sdk
RUN git clone http://github.com/dutradda/swaggerit --branch forking_from_falcon_swagger_with_redis_async /tmp/swaggerit
RUN pip install -r /tmp/swaggerit/requirements-dev.txt -r /tmp/swaggerit/requirements.txt
RUN rm -rf /tmp/swaggerit
ADD run_tests.sh /usr/bin/run-tests
ENTRYPOINT /bin/bash
SWAGGERIT_DEV_HOME = $(shell pwd)

.PHONY: all build test up-services up down-services down stop-services stop

all: build test

build: docker/Dockerfile docker/docker-compose.yml
	docker-compose -f ./docker/docker-compose.yml build swaggerit

test:
	docker-compose -f ./docker/docker-compose.yml run -e TOXENV=${TOX} swaggerit run-tests

up-services up:
	docker-compose -f ./docker/docker-compose-services.yml up -d mysql redis elsearch

down-services down:
	docker-compose -f ./docker/docker-compose-services.yml down

stop-services stop:
	docker-compose -f ./docker/docker-compose-services.yml stop mysql redis elsearch

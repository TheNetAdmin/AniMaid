#!/bin/bash

set -x

export DOCKER_USER="$(id -u):$(id -g)"

docker compose                        \
    -f qbittorrent/docker-compose.yml \
    -f prefect/docker-compose.yml     \
    -f mongo/docker-compose.yml       \
    --project-directory $PWD          \
    up -d                             \
;
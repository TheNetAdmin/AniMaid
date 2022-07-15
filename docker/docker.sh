#!/bin/bash

docker compose \
    -f qbittorrent/docker-compose.yml \
    -f prefect/docker-compose.yml \
    up \
    -d \
;
#!/bin/bash

set -e
set -u

# export ANIMAID_NETWORK="animaid-docker-network"
# docker network create "${ANIMAID_NETWORK}"

function export_secrets() {
    secret_file="secrets/data/secrets.json"
    for s in $(cat "${secret_file}" | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]" ); do
        export $s
    done

}

function docker_compose() {
    docker compose                        \
        -f qbittorrent/docker-compose.yml \
        -f mongo/docker-compose.yml       \
        --project-directory $PWD          \
        $*                                \
    ;
}


export_secrets
case $1 in
    up)   docker_compose up -d ;;
    down) docker_compose down  ;;
    *)    docker_compose up -d ;;
esac

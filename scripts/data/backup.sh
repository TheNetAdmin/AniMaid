#!/bin/bash

set -xe

files_to_backup=(
    "bangumi_moe"
    "download"
    "source"
)

curr_path="$(realpath "$(dirname "$0")")"
cd "${curr_path}" || exit 1

suffix=$(date +%m-%d-%y)

backup_path="backup/${suffix}"
mkdir -p "${backup_path}"

for f in "${files_to_backup[@]}"; do
    cp "${f}.json" "${backup_path}/${f}.json"
done

pushd "${backup_path}" || exit 1
    rm -f "backup-${suffix}.tar.gz"
    tar -zcvf "backup-${suffix}.tar.gz" ./*
    rm -f ./*.json
popd || exit 1
#!/bin/bash

set -x
set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 magnet_hash"
fi

echo "This script is not ready to use"
exit 2

magnet_hash=$1

curr_path="$(realpath "$(dirname "$0")")"

jq \
    ".[] | select(.magnet_hash == $magnet_hash) | {title: .title, publish_time: .publish_time}" \
    "${curr_path}/download.json"    \
    | tee "${curr_path}/gc_result.json" \
;

function backup_then_gc {
    exit 2
    bash "${curr_path}/backup.sh"
    jq "del(.[length-${num_elements}:length)" "${curr_path}/download.json" > "${curr_path}/download-gced.json"
    mv "${curr_path}/download.json"           "${curr_path}/download-pre-gc.json"
    mv "${curr_path}/download-gced.json"      "${curr_path}/download.json"
}

echo "Do you wish to delete these elements?"
select yn in "y" "n"; do
    case $yn in
        y ) backup_then_gc; break;;
        n ) exit;;
    esac
done

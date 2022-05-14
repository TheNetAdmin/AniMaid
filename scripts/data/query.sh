#!/bin/bash

# grep -i "少女与战车" bangumi_moe.json | grep "title" | grep -v "introduction" | cut -d":" -f2-

curr_path="$(realpath "$(dirname "$0")")"

jq \
    '.[] | select(.team.name | test("VCB-Studio")) | select(.title | test("Love Live") ) | {title: .title, time: .publish_time}' \
    "${curr_path}/bangumi_moe.json"    \
    | tee "${curr_path}/query_result.json" \
;
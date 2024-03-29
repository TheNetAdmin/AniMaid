#!/bin/bash

# grep -i "少女与战车" bangumi_moe.json | grep "title" | grep -v "introduction" | cut -d":" -f2-

curr_path="$(realpath "$(dirname "$0")")"

jq \
    '.[] | select(.title | test("少年歌行") ) | {title: .title, time: .publish_time, team_name: .team.name}' \
    "${curr_path}/../data/bangumi_moe.json"    \
    | tee "${curr_path}/query_result.json" \
;

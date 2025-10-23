#!/usr/bin/env bash
#
# extract_dates.sh
# ----------------
# Given a JSON file (first argument) and a team‐ID regex (second argument),
# output all unique, sorted YYYY-MM-DD values from .publish_time
# where .team._id matches the given regex and .publish_time is non-null.
#

# Exit on any error
set -euo pipefail


curr_path="$(realpath "$(dirname "$0")")"

# Usage check
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <team_id_regex>"
  exit 1
fi

TEAM_REGEX="$1"

jq -r --arg re "$TEAM_REGEX" '
  [ .[]
    | select(
        (.team != null)
        and (.team._id != null)
        and (.team._id | test($re))
        and (.publish_time != null)
      )
    | .publish_time[0:10]
  ]
  | sort
  | unique[]
' "${curr_path}/../data/bangumi_moe.json" | tee "${curr_path}/query_result.json"

# jq \
#     '[ .[] | select(.team._id | test("60313a6e32f14c000745a5e2") ) | .publish_time[0:10] ] | unique[] | sort'\
#     "${curr_path}/../data/bangumi_moe.json"    \
#     | tee "${curr_path}/query_result.json" \
# ;

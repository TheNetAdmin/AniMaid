#!/bin/bash
set -e
set -x
curr_path=$(realpath $(dirname $0))
cd "$curr_path/.."
python3 animaid.py update -a
python3 animaid.py download

ORGANIZE_MINS=60
if [ -n "${ORGANIZE_MINS}" ]; then
echo "Scheduling organizing script in ${ORGANIZE_MINS} minutes"
at now + "${ORGANIZE_MINS}" minute <<- EOF
bash ./scripts/organize.sh
EOF
fi
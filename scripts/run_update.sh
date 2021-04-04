#!/bin/bash
set -e
set -x
curr_path=$(realpath $(dirname $0))
cd "$curr_path/.."
python3 animaid.py update -a
python3 animaid.py download
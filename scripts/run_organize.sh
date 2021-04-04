#!/bin/bash
set -x
curr_path=$(realpath $(dirname $0))
cd "$curr_path/.."
python3 animaid.py organize -a
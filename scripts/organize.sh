#!/bin/bash
set -e
set -x
curr_path=$(realpath $(dirname $0))

mount -a

cd "$curr_path/.."
python3 animaid.py organize -a
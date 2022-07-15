#! /bin/bash

for s in $(cat $1 | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]" ); do
    echo $s
done

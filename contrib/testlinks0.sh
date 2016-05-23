#!/usr/bin/env bash

docker run --rm -ti --name pingme busybox sh -c "echo 'Now try testlinks1.py' ; while true ; do sleep 1 ; done"

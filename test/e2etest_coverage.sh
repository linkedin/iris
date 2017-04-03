#!/bin/bash
CURDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $(dirname ${CURDIR})
coverage run --source=iris src/iris/bin/run_server.py configs/config.dev.yaml &>/dev/null &
pid=$!
sleep 2
py.test test/e2etest.py
sleep 1
/bin/kill -INT $pid
coverage report -m

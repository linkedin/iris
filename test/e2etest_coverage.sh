#!/bin/bash
CURDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $(dirname ${CURDIR})
if [ ! -z "$SUPPORT_COMBINED_COVERAGE" ]; then
  export COVERAGE_FILE=.coverage.e2e
fi
coverage run --source=iris src/iris/bin/run_server.py configs/config.dev.yaml &>/dev/null &
pid=$!
sleep 2
if ! kill -0 "$pid" ; then
  echo Server failed to start. Bailing.
  exit 1
fi
py.test -v test/e2etest.py
sleep 1
/bin/kill -INT $pid
if [ -z "$SUPPORT_COMBINED_COVERAGE" ]; then
  coverage report -m
fi

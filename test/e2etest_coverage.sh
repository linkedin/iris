#!/bin/bash
CURDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $(dirname ${CURDIR})
if [ ! -z "$SUPPORT_COMBINED_COVERAGE" ]; then
  export COVERAGE_FILE=.coverage.e2e
fi
coverage run --concurrency=gevent --source=iris ./test/e2eserver.py configs/config.dev.yaml &>/dev/null &
pid=$!
sleep 2
if ! /bin/kill -0 "$pid" ; then
  echo Server failed to start. Bailing.
  exit 1
fi
py.test test/e2etest.py
sleep 1
/bin/kill -TERM $pid
if [ -z "$SUPPORT_COMBINED_COVERAGE" ]; then
  coverage report -m
fi

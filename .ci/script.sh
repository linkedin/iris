#!/bin/bash
set -e

CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CI_DIR}/common.sh"

make serve &
iris-sender ./configs/config.dev.yaml &
pid=$!
sleep 2
if ! /bin/kill -0 "$pid" ; then
  echo Sender failed to start. Bailing.
  exit 1
fi

make check

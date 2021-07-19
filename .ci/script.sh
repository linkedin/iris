#!/bin/bash
set -e

CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CI_DIR}/common.sh"

checkpid() {
    pid="$1"
    msg="$2"
    sleep 2
    if ! /bin/kill -0 "$pid" ; then
        echo "Failed to start: $msg. Bailing."
        exit 1
    fi
}

iris-dev ./configs/config.dev.yaml &
checkpid $! 'iris-dev'
iris-sender ./configs/config.dev.yaml &
checkpid $! 'iris-sender'

make check

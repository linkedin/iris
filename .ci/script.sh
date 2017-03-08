#!/bin/bash
CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CI_DIR}/common.sh"

pushd ${TRAVIS_BUILD_DIR}
make serve &
iris-sender ./configs/config.dev.yaml &

make check

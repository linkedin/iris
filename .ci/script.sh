#!/bin/bash
set -e

CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CI_DIR}/common.sh"

make serve &
iris-sender ./configs/config.dev.yaml &

make check

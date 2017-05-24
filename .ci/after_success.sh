#!/bin/bash
set -e

CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CI_DIR}/common.sh"

# Kill the `make serve` executed prior to this, so the e2e coverage tests
# will properly run. The sender will still be alive.
killall -9 iris-dev

make combined-cov

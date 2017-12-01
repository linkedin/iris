#!/bin/bash
set -e

CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CI_DIR}/common.sh"

bash ${CI_DIR}/run_mysql_docker.sh

echo "[*] installing app dependencies..."
sudo apt-get update
sudo apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev  # for ldap
pip install -e '.[dev,kazoo]'

bash ${CI_DIR}/setup_mysql.sh

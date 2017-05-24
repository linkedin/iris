#!/bin/bash
set -e

CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CI_DIR}/common.sh"

bash ${CI_DIR}/run_mysql_docker.sh

echo "[*] installing app dependencies..."
sudo apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev  # for ldap
python setup.py develop
echo "[*] pip installing dev_requirements.txt..."
pip install -r dev_requirements.txt

bash ${CI_DIR}/setup_mysql.sh

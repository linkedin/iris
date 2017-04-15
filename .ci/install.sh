#!/bin/bash
set -e

CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CI_DIR}/common.sh"

bash ${CI_DIR}/run_mysql_docker.sh

pushd ${TRAVIS_BUILD_DIR}
	echo "[*] installing app dependencies..."
	python setup.py develop
	echo "[*] pip installing dev_requirements.txt..."
	pip install -r dev_requirements.txt
popd

bash ${CI_DIR}/setup_mysql.sh

set +e

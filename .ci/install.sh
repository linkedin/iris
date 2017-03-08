#!/bin/bash
CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CI_DIR}/common.sh"

bash ${CI_DIR}/run_mysql_docker.sh

sudo pip install virtualenvwrapper
. /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv iris-api
workon iris-api

pushd ${TRAVIS_BUILD_DIR}
	python setup.py develop
	pip install -r dev_requirements.txt
popd

bash ${CI_DIR}/setup_mysql.sh

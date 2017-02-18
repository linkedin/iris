#!/bin/bash
CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CI_DIR}/common.sh"

bash ./run_mysql_docker.sh

sudo pip install virtualenvwrapper
. /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv iris-api
workon iris-api

pushd ${TRAVIS_BUILD_DIR}
python setup.py develop
pip install -r dev_requirements.txt
# sed -ie 's/password: ""/password: root/g' configs/config.dev.yaml

bash ./setup_mysql.sh

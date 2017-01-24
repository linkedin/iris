#!/bin/bash
CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CI_DIR}/common.sh"

echo "[*] Spinning up mysql through docker"
docker run -p 3306:3306 --name mysql \
	-e MYSQL_ALLOW_EMPTY_PASSWORD=1  \
	-e MYSQL_ROOT_HOST=172.17.0.1 \
	-d mysql/mysql-server:5.7


sudo pip install virtualenvwrapper
. /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv iris-api
workon iris-api

pushd ${TRAVIS_BUILD_DIR}
python setup.py develop
pip install -r dev_requirements.txt
# sed -ie 's/password: ""/password: root/g' configs/config.dev.yaml

for i in `seq 1 5`; do
	mysql -h 127.0.0.1 -u root -e 'show databases;' && break
	echo "[*] Waiting for mysql to start..."
	sleep 5
done

echo "[*] Setting MySQL sql_mode..."
mysql -h 127.0.0.1 -u root \
	-e "SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));"
echo "[*] Loading MySQL schema..."
mysql -h 127.0.0.1 -u root < ./db/schema_0.sql
echo "[*] Loading MySQL dummy data..."
mysql -h 127.0.0.1 -u root -o iris < ./db/dummy_data.sql

echo "[*] Tables created for database iris:"
mysql -h 127.0.0.1 -u root -o iris -e 'show tables;'

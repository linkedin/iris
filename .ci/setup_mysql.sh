#!/bin/bash

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

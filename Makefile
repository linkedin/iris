all: serve

serve:
	gunicorn --reload --access-logfile=- -b '0.0.0.0:16649' --worker-class gevent \
		-e CONFIG=./configs/config.dev.yaml \
		iris_api.wrappers.gunicorn:application

sender:
	iris-sender configs/config.dev.yaml

test:
	make unit
	make e2e

e2e:
	py.test ./test/e2etest.py

unit:
	py.test test

check:
	flake8
	make test

unit-cov:
	py.test --cov-report term-missing --cov=iris_api test

e2e-cov:
	./test/e2etest_coverage.sh

.PHONY: test

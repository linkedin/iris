all: serve

serve:
	gunicorn --reload --access-logfile=- -b '0.0.0.0:16649' --worker-class gevent \
		-e CONFIG=./configs/config.dev.yaml \
		iris.wrappers.gunicorn:application

sender:
	iris-sender configs/config.dev.yaml

test:
	make unit
	make e2e

e2e:
	py.test -vv ./test/e2etest.py

unit:
	py.test -vv test

flake8:
	flake8 src test setup.py

check:
	make flake8
	make test

unit-cov:
	COVERAGE_FILE=.coverage.unit py.test --cov-report term-missing --cov=iris test

e2e-cov:
	./test/e2etest_coverage.sh

combined-cov:
	rm -f .coverage*
	make unit-cov
	SUPPORT_COMBINED_COVERAGE=1 make e2e-cov
	coverage combine
	coverage report -m

.PHONY: test

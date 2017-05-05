all: serve

serve:
	iris-server ./configs/config.dev.yaml

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
	SUPPORT_COMBINED_COVERAGE=1 make e2e-cov
	make unit-cov
	coverage combine
	coverage report -m

.PHONY: test

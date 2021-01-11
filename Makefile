.PHONY: all clean tests stress-tests coverage test_coverage install lint docs dist check_formatting

PYTHON=python3
PYLINT=pylint
PYTESTS=pytest
COVERAGE=coverage

tests: check_formatting
	$(PYTESTS) -n auto

stress-tests: SA_STRESS_TESTS=1
stress-tests: tests
	$(PYTESTS) -n auto

clean:
	rm -rf superannotate.egg-info
	rm -rf build
	rm -rf dist
	rm -rf htmlcov

coverage: test_coverage

test_coverage: check_formatting
	-$(PYTESTS) --cov=superannotate -n auto
	$(COVERAGE) html
	@echo "\033[95m\n\nCoverage successful! View the output at file://htmlcov/index.html.\n\033[0m"

install:
	pip install .

lint: check_formatting
	-$(PYLINT) --output-format=json superannotate/ | pylint-json2html -o pylint.html

lint_tests:
	-$(PYLINT) tests/*

docs:
	cd docs && make html
	@echo "\033[95m\n\nBuild successful! View the docs homepage at file://docs/build/html/index.html.\n\033[0m"

dist:
	-rm -rf dist/*
	$(PYTHON) setup.py sdist
	twine upload dist/*

check_formatting:
	yapf -p -r --diff -e '*/pycocotools_sa' superannotate

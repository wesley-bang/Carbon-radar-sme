.PHONY: install test demo validate report

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

validate:
	python -m carbonradar.cli validate

demo:
	python -m carbonradar.cli run-demo --org ORG001 --year 2025

report:
	python -m carbonradar.cli build-report --org ORG001 --year 2025


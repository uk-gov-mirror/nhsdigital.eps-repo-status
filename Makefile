install: install-python install-hooks

install-python:
	poetry install

install-hooks: install-python
	poetry run pre-commit install --install-hooks --overwrite
clean:

deep-clean: clean
	rm -rf .venv

test:
	cd packages/get_repo_status && COVERAGE_FILE=coverage/.coverage poetry run python -m pytest

lint: lint-black lint-flake8 lint-github-actions

lint-black:
	poetry run black .

lint-flake8:
	poetry run flake8 .

lint-github-actions:
	actionlint

run-get-repo-status:
	poetry run python scripts/run_repo_status.py --output /tmp/repo_status_export.json

.PHONY: install lint build test clean
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
	COVERAGE_FILE=packages/setup_github_repo/coverage/.coverage poetry run python -m pytest -c packages/setup_github_repo/pytest.ini packages/setup_github_repo

lint: lint-black lint-flake8

lint-black:
	poetry run black .

lint-flake8:
	poetry run flake8 .


run-get-repo-status:
	GITHUB_TOKEN=`gh auth token` poetry run python scripts/run_repo_status.py --output /tmp/repo_status_export.json


%:
	@$(MAKE) -f /usr/local/share/eps/Mk/common.mk $@

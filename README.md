EPS REPO STATUS
================

Users with access can view the reports by going to: [https://nhsdigital.github.io/eps-repo-status](https://nhsdigital.github.io/eps-repo-status)

## Requirements

- Python as configured by Poetry (see `pyproject.toml`).
- `GITHUB_TOKEN` environment variable with access to the listed repositories.

## Usage

The tool now lives under `packages/get_repo_status` and can be invoked either via the
wrapper script or directly as a module.

```bash
poetry install
poetry run python scripts/get_repo_status.py --output /tmp/repo_status.json
```

You can also run the module explicitly:

```bash
poetry run python -m packages.get_repo_status --output /tmp/repo_status.json
```

### Options

- `--output` (required): Path where the JSON report should be written.
- `--repos-file`: Optional path to a JSON file containing repository metadata. It
	defaults to `packages/get_repo_status/repos.json`.

The default repository list mirrors the former inline Python structure and can be
maintained independently of the code.

"""Compatibility wrapper for the refactored GitHub repository setup package.

Usage remains the same:
    poetry run python scripts/setup_github_repos.py --gh_auth_token "$GH_TOKEN"

You can also run without passing a token; the CLI will use `gh auth token`
and fall back to `gh auth login` when needed.

The CLI also validates AWS credentials for required profiles and runs
`make aws-login` if credentials are missing or expired.
"""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.setup_github_repo.app.cli import main  # noqa: E402


if __name__ == "__main__":
    main()

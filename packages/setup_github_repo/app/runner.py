"""High-level orchestration for end-to-end GitHub repository setup tasks."""

import json
from dataclasses import asdict

from github import Github

from .aws_exports import AwsExportsService
from .github_setup import GithubSetupService
from .repo_status import RepoStatusLoader
from .secrets_builder import SecretsBuilder


class SetupGithubRepoRunner:
    """Coordinate all setup steps for target GitHub repositories."""

    def __init__(self, gh_auth_token: str):
        self._github = Github(gh_auth_token)
        self._aws_exports = AwsExportsService()
        self._repo_status_loader = RepoStatusLoader()

        github_teams = GithubSetupService.get_github_teams(github=self._github)
        self._github_setup = GithubSetupService(
            github=self._github,
            github_teams=github_teams,
        )
        self._secrets_builder = SecretsBuilder(self._aws_exports)
        self._github_teams = github_teams

    def run(self) -> None:
        secrets = self._secrets_builder.build()

        self._print_setup_summary(secrets_keys=sorted(asdict(secrets).keys()))

        repos = self._repo_status_loader.load_repo_configs()
        for repo in repos:
            self._github_setup.setup_repo(repo_config=repo, secrets=secrets)

    def _print_setup_summary(self, secrets_keys: list[str]) -> None:
        print("\n\n************************************************")
        print("************************************************")
        print(f"github_teams: {json.dumps(asdict(self._github_teams), indent=2)}")
        print("************************************************")
        print(f"secrets keys only: {json.dumps(secrets_keys, indent=2)}")
        print("************************************************")
        print("\n\n************************************************")

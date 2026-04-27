"""Shared utilities for prompting and API pacing in GitHub setup operations."""

import time

from github import Github

from .models import GithubTeams


class GithubOperationBase:
    """Shared behavior for interactive prompts and API rate-limit pacing."""

    def __init__(
        self,
        github: Github,
        github_teams: GithubTeams,
        interactive: bool = True,
        rate_limit_delay_seconds: float = 1.0,
    ):
        self._github = github
        self._github_teams = github_teams
        self._interactive = interactive
        self._rate_limit_delay_seconds = rate_limit_delay_seconds

    def _confirm_action(self, prompt: str) -> bool:
        if not self._interactive:
            return True

        response = input(prompt)
        if response.lower() == "y":
            print("Continuing...")
            return True

        print("Returning.")
        return False

    def _sleep_for_rate_limit(self) -> None:
        time.sleep(self._rate_limit_delay_seconds)

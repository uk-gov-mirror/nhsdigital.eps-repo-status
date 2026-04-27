"""Repository access permission management for standard EPS GitHub teams."""

from .github_base import GithubOperationBase
from .models import RepoConfig


class GithubAccessManager(GithubOperationBase):
    """Manage repository team access permissions."""

    def setup_access(self, repo_config: RepoConfig) -> None:
        repo_url = repo_config.repoUrl
        if not self._confirm_action(f"Setting access in repo {repo_url}. Do you want to continue? (y/N): "):
            return

        org = self._github.get_organization("NHSDigital")
        repo = self._github.get_repo(repo_url)
        team_permissions = [
            (self._github_teams.eps_team, "Write_View_Dependabot_Alerts"),
            (self._github_teams.eps_administrator_team, "admin"),
        ]

        for team_id, permission in team_permissions:
            team = org.get_team(int(team_id))
            print(f"Granting team {team.slug} access to repo {repo_url} with role {permission}")
            team.update_team_repository(repo, permission)
            self._sleep_for_rate_limit()

"""Unit tests for repository access management in GithubAccessManager."""

from unittest.mock import MagicMock, call, patch

from setup_github_repo.app.github_access import GithubAccessManager
from setup_github_repo.app.models import GithubTeams, RepoConfig


def _repo_config() -> RepoConfig:
    return RepoConfig(
        repoUrl="NHSDigital/example-repo",
        mainBranch="main",
        setTargetSpineServers=False,
        isAccountResources=False,
        setTargetServiceSearchServers=False,
        isEchoRepo=False,
        inWeeklyRelease=False,
    )


def _github_teams() -> GithubTeams:
    return GithubTeams(
        eps_administrator_team=1,
        eps_testers_team=2,
        eps_team=3,
        eps_deployments_team=4,
    )


def test_setup_access_grants_expected_team_permissions(capsys):
    fake_repo = MagicMock()
    fake_org = MagicMock()

    eps_team = MagicMock()
    eps_team.slug = "eps"
    admins_team = MagicMock()
    admins_team.slug = "eps-admin"
    fake_org.get_team.side_effect = [eps_team, admins_team]

    fake_github = MagicMock()
    fake_github.get_organization.return_value = fake_org
    fake_github.get_repo.return_value = fake_repo

    manager = GithubAccessManager(
        github=fake_github,
        github_teams=_github_teams(),
        interactive=False,
        rate_limit_delay_seconds=0,
    )
    manager._sleep_for_rate_limit = MagicMock()

    manager.setup_access(_repo_config())

    fake_github.get_organization.assert_called_once_with("NHSDigital")
    fake_github.get_repo.assert_called_once_with("NHSDigital/example-repo")
    fake_org.get_team.assert_has_calls([call(3), call(1)])

    eps_team.update_team_repository.assert_called_once_with(fake_repo, "Write_View_Dependabot_Alerts")
    admins_team.update_team_repository.assert_called_once_with(fake_repo, "admin")
    assert manager._sleep_for_rate_limit.call_count == 2

    output = capsys.readouterr().out
    assert "Granting team eps access to repo NHSDigital/example-repo with role Write_View_Dependabot_Alerts" in output
    assert "Granting team eps-admin access to repo NHSDigital/example-repo with role admin" in output


@patch("setup_github_repo.app.github_access.GithubAccessManager._confirm_action", return_value=False)
def test_setup_access_skips_when_not_confirmed(_mock_confirm_action: MagicMock):
    fake_github = MagicMock()

    manager = GithubAccessManager(
        github=fake_github,
        github_teams=_github_teams(),
        interactive=True,
        rate_limit_delay_seconds=0,
    )

    manager.setup_access(_repo_config())

    fake_github.get_organization.assert_not_called()
    fake_github.get_repo.assert_not_called()

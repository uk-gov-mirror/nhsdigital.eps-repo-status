"""Unit tests for environment setup behavior in GithubEnvironmentManager."""

from unittest.mock import MagicMock

from setup_github_repo.app.github_environments import GithubEnvironmentManager
from setup_github_repo.app.models import GithubTeams, RepoConfig


def _repo_config(
    *,
    is_account_resources: bool = False,
    is_echo_repo: bool = False,
    in_weekly_release: bool = False,
) -> RepoConfig:
    return RepoConfig(
        repoUrl="NHSDigital/example-repo",
        mainBranch="main",
        setTargetSpineServers=False,
        isAccountResources=is_account_resources,
        setTargetServiceSearchServers=False,
        isEchoRepo=is_echo_repo,
        inWeeklyRelease=in_weekly_release,
    )


def _github_teams() -> GithubTeams:
    return GithubTeams(
        eps_administrator_team=1,
        eps_testers_team=2,
        eps_team=3,
        eps_deployments_team=4,
    )


def test_setup_environments_only_creates_create_pull_request_when_not_in_weekly_release(capsys):
    fake_repo = MagicMock()
    fake_repo.name = "NHSDigital/example-repo"

    fake_github = MagicMock()
    fake_github.get_repo.return_value = fake_repo

    manager = GithubEnvironmentManager(
        github=fake_github,
        github_teams=_github_teams(),
        interactive=False,
        rate_limit_delay_seconds=0,
    )

    manager._setup_repo_environment = MagicMock()
    manager._setup_account_resources_environments = MagicMock()

    manager.setup_environments(_repo_config(in_weekly_release=False))

    assert manager._setup_repo_environment.call_count == 1
    first_environment = manager._setup_repo_environment.call_args.args[1]
    assert first_environment.name == "create_pull_request"
    manager._setup_account_resources_environments.assert_not_called()

    output = capsys.readouterr().out
    assert "not in weekly release, so not creating release environments" in output


def test_setup_environments_creates_all_release_environments_when_in_weekly_release():
    fake_repo = MagicMock()
    fake_repo.name = "NHSDigital/example-repo"

    fake_github = MagicMock()
    fake_github.get_repo.return_value = fake_repo

    manager = GithubEnvironmentManager(
        github=fake_github,
        github_teams=_github_teams(),
        interactive=False,
        rate_limit_delay_seconds=0,
    )

    manager._setup_repo_environment = MagicMock()
    manager._setup_account_resources_environments = MagicMock()

    manager.setup_environments(_repo_config(in_weekly_release=True))

    created_environment_names = [call.args[1].name for call in manager._setup_repo_environment.call_args_list]

    assert created_environment_names == [
        "create_pull_request",
        "dev",
        "ref",
        "int",
        "dev-pr",
        "recovery",
        "qa",
        "prod",
    ]
    manager._setup_account_resources_environments.assert_not_called()

"""Unit tests for GithubSetupService orchestration and team resolution."""

from unittest.mock import MagicMock, call, patch

from setup_github_repo.app.github_setup import GithubSetupService
from setup_github_repo.app.models import GithubTeams, RepoConfig, Roles, Secrets


def _repo_config() -> RepoConfig:
    return RepoConfig(
        repoUrl="NHSDigital/example-repo",
        mainBranch="main",
        setTargetSpineServers=False,
        isAccountResources=False,
        setTargetServiceSearchServers=False,
        isEchoRepo=False,
        inWeeklyRelease=True,
    )


def _roles() -> Roles:
    return Roles(
        cloud_formation_deploy_role="deploy-role",
        cloud_formation_check_version_role="check-role",
        cloud_formation_prepare_changeset_role="changeset-role",
        release_notes_execute_lambda_role="release-notes-role",
        artillery_runner_role="artillery-role",
    )


def _secrets() -> Secrets:
    roles = _roles()
    return Secrets(
        regression_test_pem="regression-pem",
        automerge_pem="automerge-pem",
        create_pull_request_pem="create-pr-pem",
        eps_multi_repo_deployment_pem="multi-repo-pem",
        dev_roles=roles,
        int_roles=roles,
        prod_roles=roles,
        qa_roles=roles,
        ref_roles=roles,
        recovery_roles=roles,
        proxygen_prod_role="proxygen-prod-role",
        proxygen_ptl_role="proxygen-ptl-role",
        dev_target_spine_server="dev-spine",
        int_target_spine_server="int-spine",
        prod_target_spine_server="prod-spine",
        qa_target_spine_server="qa-spine",
        ref_target_spine_server="ref-spine",
        recovery_target_spine_server="recovery-spine",
        dev_target_service_search_server="dev-search",
        int_target_service_search_server="int-search",
        prod_target_service_search_server="prod-search",
        qa_target_service_search_server="qa-search",
        ref_target_service_search_server="ref-search",
        recovery_target_service_search_server="recovery-search",
        dependabot_token="dependabot-token",
    )


@patch("setup_github_repo.app.github_setup.GithubRepoSettingsManager")
@patch("setup_github_repo.app.github_setup.GithubSecretManager")
@patch("setup_github_repo.app.github_setup.GithubEnvironmentManager")
@patch("setup_github_repo.app.github_setup.GithubAccessManager")
def test_init_wires_all_manager_dependencies(
    mock_access_manager: MagicMock,
    mock_environment_manager: MagicMock,
    mock_secret_manager: MagicMock,
    mock_repo_settings_manager: MagicMock,
):
    fake_github = MagicMock()
    teams = GithubTeams(
        eps_administrator_team=1,
        eps_testers_team=2,
        eps_team=3,
        eps_deployments_team=4,
    )

    GithubSetupService(
        github=fake_github,
        github_teams=teams,
        interactive=False,
        rate_limit_delay_seconds=0,
    )

    expected_call = call(
        github=fake_github,
        github_teams=teams,
        interactive=False,
        rate_limit_delay_seconds=0,
    )
    mock_access_manager.assert_called_once_with(**expected_call.kwargs)
    mock_environment_manager.assert_called_once_with(**expected_call.kwargs)
    mock_secret_manager.assert_called_once_with(**expected_call.kwargs)
    mock_repo_settings_manager.assert_called_once_with(**expected_call.kwargs)


def test_get_github_teams_reads_expected_slugs_and_returns_ids():
    fake_org = MagicMock()
    fake_org.get_team_by_slug.side_effect = [
        MagicMock(id=11),
        MagicMock(id=22),
        MagicMock(id=33),
        MagicMock(id=44),
    ]

    fake_github = MagicMock()
    fake_github.get_organization.return_value = fake_org

    teams = GithubSetupService.get_github_teams(github=fake_github)

    fake_github.get_organization.assert_called_once_with("NHSDigital")
    fake_org.get_team_by_slug.assert_has_calls(
        [
            call("eps-administrators"),
            call("eps-testers"),
            call("eps"),
            call("eps-deployments"),
        ]
    )
    assert teams == GithubTeams(
        eps_administrator_team=11,
        eps_testers_team=22,
        eps_team=33,
        eps_deployments_team=44,
    )


def test_setup_repo_calls_each_manager_with_repo_config_and_secrets():
    service = GithubSetupService.__new__(GithubSetupService)
    service._repo_settings_manager = MagicMock()
    service._access_manager = MagicMock()
    service._environment_manager = MagicMock()
    service._secret_manager = MagicMock()

    repo_config = _repo_config()
    secrets = _secrets()

    service.setup_repo(repo_config=repo_config, secrets=secrets)

    service._repo_settings_manager.setup_general_settings.assert_called_once_with(repo_config=repo_config)
    service._access_manager.setup_access.assert_called_once_with(repo_config=repo_config)
    service._environment_manager.setup_environments.assert_called_once_with(repo_config=repo_config)
    service._secret_manager.set_all_secrets.assert_called_once_with(repo_config=repo_config, secrets=secrets)

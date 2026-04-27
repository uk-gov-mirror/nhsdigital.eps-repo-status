"""Unit tests for SetupGithubRepoRunner orchestration and dependency wiring."""

from dataclasses import asdict
from unittest.mock import MagicMock, call, patch

from setup_github_repo.app.models import GithubTeams, RepoConfig, Roles, Secrets
from setup_github_repo.app.runner import SetupGithubRepoRunner


def _repo_config(repo_url: str) -> RepoConfig:
    return RepoConfig(
        repoUrl=repo_url,
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


@patch("setup_github_repo.app.runner.SecretsBuilder")
@patch("setup_github_repo.app.runner.GithubSetupService")
@patch("setup_github_repo.app.runner.RepoStatusLoader")
@patch("setup_github_repo.app.runner.AwsExportsService")
@patch("setup_github_repo.app.runner.Github")
def test_init_wires_dependencies(
    mock_github: MagicMock,
    mock_aws_exports_service: MagicMock,
    mock_repo_status_loader: MagicMock,
    mock_github_setup_service: MagicMock,
    mock_secrets_builder: MagicMock,
):
    github_instance = MagicMock()
    mock_github.return_value = github_instance
    aws_exports_instance = MagicMock()
    mock_aws_exports_service.return_value = aws_exports_instance
    github_teams = MagicMock()
    mock_github_setup_service.get_github_teams.return_value = github_teams

    runner = SetupGithubRepoRunner(gh_auth_token="token-123")

    mock_github.assert_called_once_with("token-123")
    mock_repo_status_loader.assert_called_once_with()
    mock_github_setup_service.get_github_teams.assert_called_once_with(github=github_instance)
    mock_github_setup_service.assert_called_once_with(github=github_instance, github_teams=github_teams)
    mock_secrets_builder.assert_called_once_with(aws_exports_instance)
    assert runner._github_teams == github_teams


def test_run_sets_up_all_loaded_repos():
    runner = SetupGithubRepoRunner.__new__(SetupGithubRepoRunner)
    secrets = _secrets()
    runner._secrets_builder = MagicMock()
    runner._secrets_builder.build.return_value = secrets
    runner._print_setup_summary = MagicMock()
    runner._repo_status_loader = MagicMock()
    runner._repo_status_loader.load_repo_configs.return_value = [
        _repo_config("NHSDigital/eps-aws-dashboards"),
        _repo_config("NHSDigital/other-repo"),
    ]
    runner._github_setup = MagicMock()

    runner.run()

    runner._print_setup_summary.assert_called_once_with(secrets_keys=sorted(asdict(secrets).keys()))
    runner._github_setup.setup_repo.assert_has_calls(
        [
            call(repo_config=_repo_config("NHSDigital/eps-aws-dashboards"), secrets=secrets),
            call(repo_config=_repo_config("NHSDigital/other-repo"), secrets=secrets),
        ]
    )
    assert runner._github_setup.setup_repo.call_count == 2


def test_run_skips_setup_when_no_matching_repo():
    runner = SetupGithubRepoRunner.__new__(SetupGithubRepoRunner)
    secrets = _secrets()
    runner._secrets_builder = MagicMock()
    runner._secrets_builder.build.return_value = secrets
    runner._print_setup_summary = MagicMock()
    runner._repo_status_loader = MagicMock()
    runner._repo_status_loader.load_repo_configs.return_value = [_repo_config("NHSDigital/other-repo")]
    runner._github_setup = MagicMock()

    runner.run()

    runner._github_setup.setup_repo.assert_called_once_with(
        repo_config=_repo_config("NHSDigital/other-repo"),
        secrets=secrets,
    )


def test_print_setup_summary_displays_team_and_secret_keys(capsys):
    runner = SetupGithubRepoRunner.__new__(SetupGithubRepoRunner)
    runner._github_teams = GithubTeams(
        eps_administrator_team=1,
        eps_testers_team=2,
        eps_team=3,
        eps_deployments_team=4,
    )

    runner._print_setup_summary(secrets_keys=["a_secret", "z_secret"])

    output = capsys.readouterr().out
    assert "github_teams" in output
    assert "secrets keys only" in output
    assert "a_secret" in output
    assert "z_secret" in output

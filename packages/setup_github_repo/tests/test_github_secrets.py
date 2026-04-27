"""Unit tests for weekly-release secret creation behavior in GithubSecretManager."""

from unittest.mock import MagicMock

from setup_github_repo.app.github_secrets import GithubSecretManager
from setup_github_repo.app.models import Roles, Secrets, RepoConfig


def _repo_config(
    *,
    in_weekly_release: bool,
    set_target_spine_servers: bool = False,
    set_target_service_search_servers: bool = False,
    is_account_resources: bool = False,
    is_echo_repo: bool = False,
) -> RepoConfig:
    return RepoConfig(
        repoUrl="NHSDigital/example-repo",
        mainBranch="main",
        setTargetSpineServers=set_target_spine_servers,
        isAccountResources=is_account_resources,
        setTargetServiceSearchServers=set_target_service_search_servers,
        isEchoRepo=is_echo_repo,
        inWeeklyRelease=in_weekly_release,
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


def test_set_all_secrets_only_creates_baseline_secrets_when_not_in_weekly_release(capsys):
    fake_repo = MagicMock()
    fake_repo.full_name = "NHSDigital/example-repo"

    fake_github = MagicMock()
    fake_github.get_repo.return_value = fake_repo

    manager = GithubSecretManager(
        github=fake_github,
        github_teams=MagicMock(),  # type: ignore[arg-type]
        interactive=False,
        rate_limit_delay_seconds=0,
    )

    manager._set_secret = MagicMock()
    manager._set_environment_secret = MagicMock()
    manager._set_role_secrets = MagicMock()

    manager.set_all_secrets(_repo_config(in_weekly_release=False), _secrets())

    set_secret_names = [call.kwargs["secret_name"] for call in manager._set_secret.call_args_list]
    assert set_secret_names == ["DEPENDABOT_TOKEN"]

    set_environment_secret_names = [
        call.kwargs["secret_name"] for call in manager._set_environment_secret.call_args_list
    ]
    assert set_environment_secret_names == [
        "AUTOMERGE_PEM",
        "AUTOMERGE_APP_ID",
        "CREATE_PULL_REQUEST_PEM",
        "CREATE_PULL_REQUEST_APP_ID",
    ]

    manager._set_role_secrets.assert_not_called()
    fake_github.get_repo.assert_called_once_with("NHSDigital/example-repo")

    output = capsys.readouterr().out
    assert "not in weekly release, so not creating additional secrets" in output


def test_set_all_secrets_creates_additional_secrets_when_in_weekly_release():
    fake_repo = MagicMock()
    fake_repo.full_name = "NHSDigital/example-repo"

    fake_github = MagicMock()
    fake_github.get_repo.return_value = fake_repo

    manager = GithubSecretManager(
        github=fake_github,
        github_teams=MagicMock(),  # type: ignore[arg-type]
        interactive=False,
        rate_limit_delay_seconds=0,
    )

    manager._set_secret = MagicMock()
    manager._set_environment_secret = MagicMock()
    manager._set_role_secrets = MagicMock()

    manager.set_all_secrets(_repo_config(in_weekly_release=True), _secrets())

    set_secret_names = [call.kwargs["secret_name"] for call in manager._set_secret.call_args_list]
    assert "DEPENDABOT_TOKEN" in set_secret_names
    assert "DEV_CLOUD_FORMATION_EXECUTE_LAMBDA_ROLE" in set_secret_names
    assert "REGRESSION_TESTS_PEM" in set_secret_names
    assert "REF_ARTILLERY_RUNNER_ROLE" in set_secret_names

    role_env_names = [call.kwargs["env_name"] for call in manager._set_role_secrets.call_args_list]
    assert role_env_names == ["DEV", "INT", "PROD", "QA", "REF", "RECOVERY"]

    fake_github.get_repo.assert_called_once_with("NHSDigital/example-repo")


def test_set_all_secrets_sets_target_spine_server_secrets_when_enabled():
    fake_repo = MagicMock()
    fake_repo.full_name = "NHSDigital/example-repo"

    fake_github = MagicMock()
    fake_github.get_repo.return_value = fake_repo

    manager = GithubSecretManager(
        github=fake_github,
        github_teams=MagicMock(),  # type: ignore[arg-type]
        interactive=False,
        rate_limit_delay_seconds=0,
    )

    manager._set_secret = MagicMock()
    manager._set_environment_secret = MagicMock()
    manager._set_role_secrets = MagicMock()

    manager.set_all_secrets(
        _repo_config(in_weekly_release=True, set_target_spine_servers=True),
        _secrets(),
    )

    set_secret_names = [call.kwargs["secret_name"] for call in manager._set_secret.call_args_list]
    assert "DEV_TARGET_SPINE_SERVER" in set_secret_names
    assert "INT_TARGET_SPINE_SERVER" in set_secret_names
    assert "PROD_TARGET_SPINE_SERVER" in set_secret_names
    assert "QA_TARGET_SPINE_SERVER" in set_secret_names
    assert "REF_TARGET_SPINE_SERVER" in set_secret_names
    assert "RECOVERY_TARGET_SPINE_SERVER" in set_secret_names


def test_set_all_secrets_sets_target_service_search_secrets_when_enabled():
    fake_repo = MagicMock()
    fake_repo.full_name = "NHSDigital/example-repo"

    fake_github = MagicMock()
    fake_github.get_repo.return_value = fake_repo

    manager = GithubSecretManager(
        github=fake_github,
        github_teams=MagicMock(),  # type: ignore[arg-type]
        interactive=False,
        rate_limit_delay_seconds=0,
    )

    manager._set_secret = MagicMock()
    manager._set_environment_secret = MagicMock()
    manager._set_role_secrets = MagicMock()

    manager.set_all_secrets(
        _repo_config(in_weekly_release=True, set_target_service_search_servers=True),
        _secrets(),
    )

    set_secret_names = [call.kwargs["secret_name"] for call in manager._set_secret.call_args_list]
    assert "DEV_TARGET_SERVICE_SEARCH_SERVER" in set_secret_names
    assert "INT_TARGET_SERVICE_SEARCH_SERVER" in set_secret_names
    assert "PROD_TARGET_SERVICE_SEARCH_SERVER" in set_secret_names
    assert "QA_TARGET_SERVICE_SEARCH_SERVER" in set_secret_names
    assert "REF_TARGET_SERVICE_SEARCH_SERVER" in set_secret_names
    assert "RECOVERY_TARGET_SERVICE_SEARCH_SERVER" in set_secret_names

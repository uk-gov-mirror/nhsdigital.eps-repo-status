"""Unit tests for CLI auth/bootstrap behavior and runner invocation."""

import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

cli = importlib.import_module("setup_github_repo.app.cli")


def test_resolve_gh_auth_token_returns_explicit_value():
    token = cli.resolve_gh_auth_token("explicit-token")

    assert token == "explicit-token"


@patch("setup_github_repo.app.cli._read_gh_auth_token", return_value="existing-token")
@patch("setup_github_repo.app.cli.subprocess.run")
def test_get_or_create_uses_existing_token(mock_subprocess_run: MagicMock, _mock_read_token: MagicMock):
    token = cli._get_or_create_gh_auth_token()

    assert token == "existing-token"
    mock_subprocess_run.assert_not_called()


@patch("setup_github_repo.app.cli._read_gh_auth_token", side_effect=[None, "new-token"])
@patch("setup_github_repo.app.cli.subprocess.run")
def test_get_or_create_runs_login_when_token_missing(
    mock_subprocess_run: MagicMock,
    _mock_read_token: MagicMock,
):
    token = cli._get_or_create_gh_auth_token()

    assert token == "new-token"
    mock_subprocess_run.assert_called_once_with(["gh", "auth", "login"], check=True)


@patch("setup_github_repo.app.cli._read_gh_auth_token", side_effect=[None, None])
@patch("setup_github_repo.app.cli.subprocess.run")
def test_get_or_create_raises_if_login_does_not_provide_token(
    _mock_subprocess_run: MagicMock,
    _mock_read_token: MagicMock,
):
    with pytest.raises(RuntimeError):
        cli._get_or_create_gh_auth_token()


@patch("setup_github_repo.app.cli._has_valid_aws_credentials_for_profile", return_value=True)
def test_get_invalid_aws_profiles_returns_empty_when_all_valid(_mock_has_valid_profile: MagicMock):
    invalid_profiles = cli._get_invalid_aws_profiles()

    assert invalid_profiles == []


@patch("setup_github_repo.app.cli._get_invalid_aws_profiles", return_value=[])
@patch("setup_github_repo.app.cli.subprocess.run")
def test_ensure_aws_credentials_skips_login_when_valid(
    mock_subprocess_run: MagicMock,
    _mock_get_invalid_profiles: MagicMock,
):
    cli.ensure_aws_credentials()

    mock_subprocess_run.assert_not_called()


@patch("setup_github_repo.app.cli._get_invalid_aws_profiles", side_effect=[["prescription-dev"], []])
@patch("setup_github_repo.app.cli.subprocess.run")
def test_ensure_aws_credentials_runs_make_login_when_invalid(
    mock_subprocess_run: MagicMock,
    _mock_get_invalid_profiles: MagicMock,
):
    cli.ensure_aws_credentials()

    mock_subprocess_run.assert_called_once_with(["make", "aws-login"], check=True)


@patch(
    "setup_github_repo.app.cli._get_invalid_aws_profiles",
    side_effect=[["prescription-dev"], ["prescription-dev"]],
)
@patch("setup_github_repo.app.cli.subprocess.run")
def test_ensure_aws_credentials_raises_if_still_invalid_after_login(
    _mock_subprocess_run: MagicMock,
    _mock_get_invalid_profiles: MagicMock,
):
    with pytest.raises(RuntimeError):
        cli.ensure_aws_credentials()


@patch("setup_github_repo.app.cli.SetupGithubRepoRunner")
@patch("setup_github_repo.app.cli.ensure_aws_credentials")
@patch("setup_github_repo.app.cli.resolve_gh_auth_token", return_value="resolved-token")
@patch("setup_github_repo.app.cli.argparse.ArgumentParser.parse_args")
def test_main_resolves_token_and_runs(
    mock_parse_args: MagicMock,
    mock_resolve_token: MagicMock,
    mock_ensure_aws_credentials: MagicMock,
    mock_runner_class: MagicMock,
):
    mock_parse_args.return_value = SimpleNamespace(gh_auth_token=None)
    mock_runner_instance = MagicMock()
    mock_runner_class.return_value = mock_runner_instance

    cli.main()

    mock_ensure_aws_credentials.assert_called_once_with()
    mock_resolve_token.assert_called_once_with(None)
    mock_runner_class.assert_called_once_with(gh_auth_token="resolved-token")
    mock_runner_instance.run.assert_called_once()

"""Unit tests for repository-level settings updates in GithubRepoSettingsManager."""

from unittest.mock import MagicMock, call, patch

from setup_github_repo.app.github_repo_settings import GithubRepoSettingsManager
from setup_github_repo.app.models import RepoConfig


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


def test_setup_general_settings_applies_expected_pr_options():
    fake_required_status_checks = MagicMock()
    fake_required_status_checks.checks = [MagicMock(context="build", app_id=123)]

    fake_branch = MagicMock()
    fake_branch.get_required_status_checks.return_value = fake_required_status_checks
    fake_branch.get_required_signatures.return_value = False

    fake_repo = MagicMock()
    fake_repo.get_branch.return_value = fake_branch
    fake_repo.private = False

    fake_requester = MagicMock()
    fake_requester.requestJsonAndCheck.side_effect = [
        ({}, {"default_workflow_permissions": "read"}),
        ({}, {}),
        ({}, {}),
    ]
    fake_repo._requester = fake_requester

    fake_github = MagicMock()
    fake_github.get_repo.return_value = fake_repo

    manager = GithubRepoSettingsManager(
        github=fake_github,
        github_teams={},  # type: ignore[arg-type]
        interactive=False,
        rate_limit_delay_seconds=0,
    )

    manager.setup_general_settings(_repo_config())

    fake_github.get_repo.assert_called_once_with("NHSDigital/example-repo")
    fake_repo.edit.assert_called_once_with(
        allow_merge_commit=False,
        allow_squash_merge=True,
        allow_rebase_merge=False,
        allow_auto_merge=True,
        delete_branch_on_merge=True,
        squash_merge_commit_title="PR_TITLE",
        squash_merge_commit_message="PR_BODY",
    )
    fake_repo.get_branch.assert_called_once_with("main")
    fake_branch.edit_protection.assert_called_once_with(
        strict=True,
        required_approving_review_count=1,
        dismiss_stale_reviews=True,
        require_last_push_approval=True,
        checks=[("build", 123)],
    )
    fake_branch.add_required_signatures.assert_called_once_with()
    fake_requester.requestJsonAndCheck.assert_has_calls(
        [
            call("GET", "/repos/NHSDigital/example-repo/actions/permissions/workflow"),
            call(
                "PUT",
                "/repos/NHSDigital/example-repo/actions/permissions/workflow",
                input={
                    "default_workflow_permissions": "read",
                    "can_approve_pull_request_reviews": True,
                },
            ),
            call(
                "PUT",
                "/repos/NHSDigital/example-repo/actions/permissions/fork-pr-contributor-approval",
                input={"approval_policy": "all_external_contributors"},
            ),
        ]
    )


def test_setup_general_settings_uses_contexts_when_checks_not_present():
    fake_required_status_checks = MagicMock()
    fake_required_status_checks.checks = []
    fake_required_status_checks.contexts = ["build", "test"]

    fake_branch = MagicMock()
    fake_branch.get_required_status_checks.return_value = fake_required_status_checks
    fake_branch.get_required_signatures.return_value = True

    fake_repo = MagicMock()
    fake_repo.get_branch.return_value = fake_branch
    fake_repo.private = True

    fake_requester = MagicMock()
    fake_requester.requestJsonAndCheck.side_effect = [
        ({}, {"default_workflow_permissions": "write"}),
        ({}, {}),
    ]
    fake_repo._requester = fake_requester
    fake_github = MagicMock()
    fake_github.get_repo.return_value = fake_repo

    manager = GithubRepoSettingsManager(
        github=fake_github,
        github_teams={},  # type: ignore[arg-type]
        interactive=False,
        rate_limit_delay_seconds=0,
    )

    manager.setup_general_settings(_repo_config())

    fake_branch.edit_protection.assert_called_once_with(
        strict=True,
        required_approving_review_count=1,
        dismiss_stale_reviews=True,
        require_last_push_approval=True,
        checks=["build", "test"],
    )
    fake_branch.add_required_signatures.assert_not_called()
    fake_requester.requestJsonAndCheck.assert_has_calls(
        [
            call("GET", "/repos/NHSDigital/example-repo/actions/permissions/workflow"),
            call(
                "PUT",
                "/repos/NHSDigital/example-repo/actions/permissions/workflow",
                input={
                    "default_workflow_permissions": "write",
                    "can_approve_pull_request_reviews": True,
                },
            ),
        ]
    )


@patch(
    "setup_github_repo.app.github_repo_settings.GithubRepoSettingsManager._confirm_action",
    return_value=False,
)
def test_setup_general_settings_skips_when_not_confirmed(_mock_confirm_action: MagicMock):
    fake_repo = MagicMock()
    fake_github = MagicMock()
    fake_github.get_repo.return_value = fake_repo

    manager = GithubRepoSettingsManager(
        github=fake_github,
        github_teams={},  # type: ignore[arg-type]
        interactive=True,
        rate_limit_delay_seconds=0,
    )

    manager.setup_general_settings(_repo_config())

    fake_github.get_repo.assert_not_called()
    fake_repo.edit.assert_not_called()

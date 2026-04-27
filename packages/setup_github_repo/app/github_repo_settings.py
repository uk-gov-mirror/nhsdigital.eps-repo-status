"""Repository-level settings management, including pull request merge options."""

from typing import Any

from .github_base import GithubOperationBase
from .models import RepoConfig


class GithubRepoSettingsManager(GithubOperationBase):
    """Handles repository settings that are not access, environments, or secrets."""

    def setup_general_settings(self, repo_config: RepoConfig) -> None:
        repo_url = repo_config.repoUrl
        main_branch = repo_config.mainBranch
        if not self._confirm_action(f"Setting general settings in repo {repo_url}. Do you want to continue? (y/N): "):
            return

        print(f"Applying general repository settings in {repo_url}")
        repo = self._github.get_repo(repo_url)
        repo.edit(
            allow_merge_commit=False,
            allow_squash_merge=True,
            allow_rebase_merge=False,
            allow_auto_merge=True,
            delete_branch_on_merge=True,
            squash_merge_commit_title="PR_TITLE",
            squash_merge_commit_message="PR_BODY",
        )

        self._set_actions_permissions(repo=repo, repo_url=repo_url)

        print(f"Applying branch protection to {repo_url} branch {main_branch}")
        branch = repo.get_branch(main_branch)
        checks = self._get_existing_required_checks(branch)
        branch.edit_protection(
            strict=True,
            required_approving_review_count=1,
            dismiss_stale_reviews=True,
            require_last_push_approval=True,
            checks=checks,
        )

        if not branch.get_required_signatures():
            branch.add_required_signatures()

        self._sleep_for_rate_limit()
        print(f"General repository settings applied in {repo_url}")

    def _set_actions_permissions(self, repo: Any, repo_url: str) -> None:
        workflow_permissions_endpoint = f"/repos/{repo_url}/actions/permissions/workflow"
        _headers, workflow_permissions = repo._requester.requestJsonAndCheck("GET", workflow_permissions_endpoint)
        default_workflow_permissions = str(workflow_permissions.get("default_workflow_permissions") or "read")

        repo._requester.requestJsonAndCheck(
            "PUT",
            workflow_permissions_endpoint,
            input={
                "default_workflow_permissions": default_workflow_permissions,
                "can_approve_pull_request_reviews": True,
            },
        )

        if not getattr(repo, "private", True):
            repo._requester.requestJsonAndCheck(
                "PUT",
                f"/repos/{repo_url}/actions/permissions/fork-pr-contributor-approval",
                input={"approval_policy": "all_external_contributors"},
            )

    def _get_existing_required_checks(self, branch: Any) -> list[str | tuple[str, int]]:
        try:
            required_status_checks = branch.get_required_status_checks()
        except Exception:
            return []

        checks = getattr(required_status_checks, "checks", None)
        if checks:
            return [(check.context, check.app_id) if check.app_id is not None else check.context for check in checks]

        return list(getattr(required_status_checks, "contexts", []))

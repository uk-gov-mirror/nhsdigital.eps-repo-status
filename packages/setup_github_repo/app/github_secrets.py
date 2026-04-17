"""Secret and environment-secret provisioning for EPS repository automation."""

import os

from github.Repository import Repository

from .constants import AUTOMERGE_APP_ID, CREATE_PULL_REQUEST_APP_ID
from .github_base import GithubOperationBase
from .models import RepoConfig, Roles, Secrets


class GithubSecretManager(GithubOperationBase):
    """Manage Actions/Dependabot/environment secrets for EPS repositories."""

    def set_all_secrets(self, repo_config: RepoConfig, secrets: Secrets) -> None:
        repo_url = repo_config.repoUrl
        if not self._confirm_action(f"Setting secrets in repo {repo_url}. Do you want to continue? (y/N): "):
            return

        repo = self._github.get_repo(repo_url)

        self._set_environment_secret(
            repo=repo,
            environment_name="create_pull_request",
            secret_name="AUTOMERGE_PEM",
            secret_value=secrets.automerge_pem,
        )
        self._set_environment_secret(
            repo=repo,
            environment_name="create_pull_request",
            secret_name="AUTOMERGE_APP_ID",
            secret_value=AUTOMERGE_APP_ID,
        )
        self._set_secret(
            repo=repo,
            secret_name="DEPENDABOT_TOKEN",
            secret_value=secrets.dependabot_token,
            set_dependabot=True,
        )
        self._set_environment_secret(
            repo=repo,
            environment_name="create_pull_request",
            secret_name="CREATE_PULL_REQUEST_PEM",
            secret_value=secrets.create_pull_request_pem,
        )
        self._set_environment_secret(
            repo=repo,
            environment_name="create_pull_request",
            secret_name="CREATE_PULL_REQUEST_APP_ID",
            secret_value=CREATE_PULL_REQUEST_APP_ID,
        )

        if not repo_config.inWeeklyRelease:
            print(f"Repo {repo_url} is not in weekly release, so not creating additional secrets.")
            return

        self._set_secret(
            repo=repo,
            secret_name="DEV_CLOUD_FORMATION_EXECUTE_LAMBDA_ROLE",
            secret_value=secrets.dev_roles.release_notes_execute_lambda_role,
            set_dependabot=False,
        )

        if repo_config.isEchoRepo:
            print(f"All required secrets set for echo repo {repo_url}.")
            return

        self._set_secret(
            repo=repo,
            secret_name="REGRESSION_TESTS_PEM",
            secret_value=secrets.regression_test_pem,
            set_dependabot=True,
        )
        self._set_secret(
            repo=repo,
            secret_name="APIM_STATUS_API_KEY",
            secret_value=os.environ.get("apim_status_api_key"),
            set_dependabot=True,
        )

        self._set_secret(
            repo=repo,
            secret_name="PROXYGEN_PTL_ROLE",
            secret_value=secrets.proxygen_ptl_role,
            set_dependabot=True,
        )
        self._set_secret(
            repo=repo,
            secret_name="PROXYGEN_PROD_ROLE",
            secret_value=secrets.proxygen_prod_role,
            set_dependabot=True,
        )

        self._set_secret(
            repo=repo,
            secret_name="DEV_ARTILLERY_RUNNER_ROLE",
            secret_value=secrets.dev_roles.artillery_runner_role,
            set_dependabot=True,
        )
        self._set_secret(
            repo=repo,
            secret_name="REF_ARTILLERY_RUNNER_ROLE",
            secret_value=secrets.ref_roles.artillery_runner_role,
            set_dependabot=False,
        )

        self._set_role_secrets(repo=repo, roles=secrets.dev_roles, env_name="DEV", set_dependabot=True)
        self._set_role_secrets(repo=repo, roles=secrets.int_roles, env_name="INT", set_dependabot=False)
        self._set_role_secrets(repo=repo, roles=secrets.prod_roles, env_name="PROD", set_dependabot=False)
        self._set_role_secrets(repo=repo, roles=secrets.qa_roles, env_name="QA", set_dependabot=False)
        self._set_role_secrets(repo=repo, roles=secrets.ref_roles, env_name="REF", set_dependabot=False)
        self._set_role_secrets(
            repo=repo,
            roles=secrets.recovery_roles,
            env_name="RECOVERY",
            set_dependabot=False,
        )

        if repo_config.setTargetSpineServers:
            self._set_secret(
                repo=repo,
                secret_name="DEV_TARGET_SPINE_SERVER",
                secret_value=secrets.dev_target_spine_server,
                set_dependabot=True,
            )
            self._set_secret(
                repo=repo,
                secret_name="REF_TARGET_SPINE_SERVER",
                secret_value=secrets.ref_target_spine_server,
                set_dependabot=False,
            )
            self._set_secret(
                repo=repo,
                secret_name="QA_TARGET_SPINE_SERVER",
                secret_value=secrets.qa_target_spine_server,
                set_dependabot=False,
            )
            self._set_secret(
                repo=repo,
                secret_name="INT_TARGET_SPINE_SERVER",
                secret_value=secrets.int_target_spine_server,
                set_dependabot=False,
            )
            self._set_secret(
                repo=repo,
                secret_name="PROD_TARGET_SPINE_SERVER",
                secret_value=secrets.prod_target_spine_server,
                set_dependabot=False,
            )
            self._set_secret(
                repo=repo,
                secret_name="RECOVERY_TARGET_SPINE_SERVER",
                secret_value=secrets.recovery_target_spine_server,
                set_dependabot=False,
            )

        if repo_config.setTargetServiceSearchServers:
            self._set_secret(
                repo=repo,
                secret_name="DEV_TARGET_SERVICE_SEARCH_SERVER",
                secret_value=secrets.dev_target_service_search_server,
                set_dependabot=True,
            )
            self._set_secret(
                repo=repo,
                secret_name="INT_TARGET_SERVICE_SEARCH_SERVER",
                secret_value=secrets.int_target_service_search_server,
                set_dependabot=False,
            )
            self._set_secret(
                repo=repo,
                secret_name="REF_TARGET_SERVICE_SEARCH_SERVER",
                secret_value=secrets.ref_target_service_search_server,
                set_dependabot=False,
            )
            self._set_secret(
                repo=repo,
                secret_name="QA_TARGET_SERVICE_SEARCH_SERVER",
                secret_value=secrets.qa_target_service_search_server,
                set_dependabot=False,
            )
            self._set_secret(
                repo=repo,
                secret_name="PROD_TARGET_SERVICE_SEARCH_SERVER",
                secret_value=secrets.prod_target_service_search_server,
                set_dependabot=False,
            )
            self._set_secret(
                repo=repo,
                secret_name="RECOVERY_TARGET_SERVICE_SEARCH_SERVER",
                secret_value=secrets.recovery_target_service_search_server,
                set_dependabot=False,
            )

    def _set_secret(
        self,
        repo: Repository,
        secret_name: str,
        secret_value: str | None,
        set_dependabot: bool,
    ) -> None:
        if secret_value is None:
            print(f"Secret value for {secret_name} in repo {repo.full_name} is not set. Not setting")
            return

        print(f"Setting value for {secret_name} in repo {repo.full_name}")
        repo.create_secret(secret_name=secret_name, unencrypted_value=secret_value, secret_type="actions")
        self._sleep_for_rate_limit()

        if set_dependabot:
            print(f"Setting value for {secret_name} in repo {repo.full_name} for dependabot")
            repo.create_secret(secret_name=secret_name, unencrypted_value=secret_value, secret_type="dependabot")
            self._sleep_for_rate_limit()

    def _set_environment_secret(
        self,
        repo: Repository,
        environment_name: str,
        secret_name: str,
        secret_value: str | None,
    ) -> None:
        if secret_value is None:
            print(f"Secret value for {secret_name} in repo {repo.full_name} is not set. Not setting")
            return

        environment = repo.get_environment(environment_name)
        print(f"Setting value for {secret_name} in repo {repo.full_name} for environment {environment_name}")
        environment.create_secret(secret_name=secret_name, unencrypted_value=secret_value)
        self._sleep_for_rate_limit()

    def _set_role_secrets(self, repo: Repository, roles: Roles, env_name: str, set_dependabot: bool) -> None:
        self._set_secret(
            repo=repo,
            secret_name=f"{env_name}_CLOUD_FORMATION_DEPLOY_ROLE",
            secret_value=roles.cloud_formation_deploy_role,
            set_dependabot=set_dependabot,
        )
        self._set_secret(
            repo=repo,
            secret_name=f"{env_name}_CLOUD_FORMATION_CHECK_VERSION_ROLE",
            secret_value=roles.cloud_formation_check_version_role,
            set_dependabot=set_dependabot,
        )
        self._set_secret(
            repo=repo,
            secret_name=f"{env_name}_CLOUD_FORMATION_CREATE_CHANGESET_ROLE",
            secret_value=roles.cloud_formation_prepare_changeset_role,
            set_dependabot=set_dependabot,
        )

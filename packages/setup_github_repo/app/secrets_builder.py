"""Builds the consolidated secrets payload from files, exports, and environment values."""

import os
from pathlib import Path
from typing import Any

from .aws_exports import AwsExportsService
from .constants import AWS_PROFILE_BY_ENV, TARGET_SERVICE_SEARCH_SERVERS, TARGET_SPINE_SERVERS
from .models import Roles, Secrets


class SecretsBuilder:
    """Build the complete secrets payload from AWS exports, local files, and env vars."""

    def __init__(self, aws_exports: AwsExportsService, secrets_directory: Path | None = None):
        self._aws_exports = aws_exports
        self._secrets_directory = secrets_directory or Path(".secrets")

    def build(self) -> Secrets:
        exports_by_env: dict[str, list[dict[str, Any]]] = {
            env_name: self._aws_exports.get_all_exports(profile_name)
            for env_name, profile_name in AWS_PROFILE_BY_ENV.items()
        }

        roles_by_env: dict[str, Roles] = {
            env_name: self._to_roles(self._aws_exports.get_role_exports(exports))
            for env_name, exports in exports_by_env.items()
        }

        prod_exports = exports_by_env["prod"]
        proxygen_ptl_role = self._aws_exports.get_named_export(
            all_exports=prod_exports,
            export_name="ci-resources:ProxygenPTLRole",
            required=True,
        )
        proxygen_prod_role = self._aws_exports.get_named_export(
            all_exports=prod_exports,
            export_name="ci-resources:ProxygenProdRole",
            required=True,
        )

        return Secrets(
            regression_test_pem=self._read_secret_file("regression_test_app.pem"),
            eps_multi_repo_deployment_pem=self._read_secret_file("eps_multi_repo_deployment.pem"),
            automerge_pem=self._read_secret_file("automerge.pem"),
            create_pull_request_pem=self._read_secret_file("create_pull_request.pem"),
            dev_roles=roles_by_env["dev"],
            int_roles=roles_by_env["int"],
            prod_roles=roles_by_env["prod"],
            qa_roles=roles_by_env["qa"],
            ref_roles=roles_by_env["ref"],
            recovery_roles=roles_by_env["recovery"],
            proxygen_prod_role=proxygen_prod_role,
            proxygen_ptl_role=proxygen_ptl_role,
            dev_target_spine_server=TARGET_SPINE_SERVERS["dev"],
            int_target_spine_server=TARGET_SPINE_SERVERS["int"],
            prod_target_spine_server=TARGET_SPINE_SERVERS["prod"],
            qa_target_spine_server=TARGET_SPINE_SERVERS["qa"],
            ref_target_spine_server=TARGET_SPINE_SERVERS["ref"],
            recovery_target_spine_server=TARGET_SPINE_SERVERS["recovery"],
            dev_target_service_search_server=TARGET_SERVICE_SEARCH_SERVERS["dev"],
            int_target_service_search_server=TARGET_SERVICE_SEARCH_SERVERS["int"],
            prod_target_service_search_server=TARGET_SERVICE_SEARCH_SERVERS["prod"],
            qa_target_service_search_server=TARGET_SERVICE_SEARCH_SERVERS["qa"],
            ref_target_service_search_server=TARGET_SERVICE_SEARCH_SERVERS["ref"],
            recovery_target_service_search_server=TARGET_SERVICE_SEARCH_SERVERS["recovery"],
            dependabot_token=os.environ.get("dependabot_token"),
        )

    @staticmethod
    def _to_roles(role_exports: Roles | dict[str, str | None]) -> Roles:
        if isinstance(role_exports, Roles):
            return role_exports
        return Roles(**role_exports)

    def _read_secret_file(self, file_name: str) -> str:
        file_path = self._secrets_directory / file_name
        return file_path.read_text(encoding="utf-8")

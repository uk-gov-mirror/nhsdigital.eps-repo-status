"""Unit tests for secrets payload creation from exports, files, and environment."""

import os
from pathlib import Path
import tempfile
from unittest.mock import patch

import pytest

from setup_github_repo.app.constants import AWS_PROFILE_BY_ENV
from setup_github_repo.app.models import Roles
from setup_github_repo.app.secrets_builder import SecretsBuilder


class StubAwsExportsService:
    def __init__(self):
        self.requested_profiles: list[str] = []
        self.get_named_export_calls: list[tuple[str, bool]] = []

    def get_all_exports(self, profile_name: str):
        self.requested_profiles.append(profile_name)
        return [
            {"Name": "ci-resources:CloudFormationDeployRole", "Value": f"{profile_name}-deploy"},
            {"Name": "ci-resources:CloudFormationCheckVersionRole", "Value": f"{profile_name}-check"},
            {"Name": "ci-resources:CloudFormationPrepareChangesetRole", "Value": f"{profile_name}-changeset"},
            {"Name": "ci-resources:ReleaseNotesExecuteLambdaRole", "Value": f"{profile_name}-release"},
            {"Name": "ci-resources:ArtilleryRunnerRole", "Value": f"{profile_name}-artillery"},
            {"Name": "ci-resources:ProxygenPTLRole", "Value": "ptl-role-arn"},
            {"Name": "ci-resources:ProxygenProdRole", "Value": "prod-role-arn"},
        ]

    def get_role_exports(self, all_exports):
        def _find(name: str):
            return next(export["Value"] for export in all_exports if export["Name"] == name)

        return Roles(
            cloud_formation_deploy_role=_find("ci-resources:CloudFormationDeployRole"),
            cloud_formation_check_version_role=_find("ci-resources:CloudFormationCheckVersionRole"),
            cloud_formation_prepare_changeset_role=_find("ci-resources:CloudFormationPrepareChangesetRole"),
            release_notes_execute_lambda_role=_find("ci-resources:ReleaseNotesExecuteLambdaRole"),
            artillery_runner_role=_find("ci-resources:ArtilleryRunnerRole"),
        )

    def get_named_export(self, all_exports, export_name: str, required: bool):
        self.get_named_export_calls.append((export_name, required))
        return next(export["Value"] for export in all_exports if export["Name"] == export_name)


def test_build_returns_complete_secrets_payload():
    with tempfile.TemporaryDirectory() as temp_dir:
        secrets_dir = Path(temp_dir)
        (secrets_dir / "regression_test_app.pem").write_text("regression", encoding="utf-8")
        (secrets_dir / "eps_multi_repo_deployment.pem").write_text("multi-repo", encoding="utf-8")
        (secrets_dir / "automerge.pem").write_text("automerge", encoding="utf-8")
        (secrets_dir / "create_pull_request.pem").write_text("create-pr", encoding="utf-8")

        aws_exports = StubAwsExportsService()
        builder = SecretsBuilder(aws_exports=aws_exports, secrets_directory=secrets_dir)

        with patch.dict(os.environ, {"dependabot_token": "token-123"}, clear=False):
            result = builder.build()

    assert result.regression_test_pem == "regression"
    assert result.eps_multi_repo_deployment_pem == "multi-repo"
    assert result.automerge_pem == "automerge"
    assert result.create_pull_request_pem == "create-pr"
    assert result.proxygen_ptl_role == "ptl-role-arn"
    assert result.proxygen_prod_role == "prod-role-arn"
    assert result.dependabot_token == "token-123"

    assert set(aws_exports.requested_profiles) == set(AWS_PROFILE_BY_ENV.values())
    assert ("ci-resources:ProxygenPTLRole", True) in aws_exports.get_named_export_calls
    assert ("ci-resources:ProxygenProdRole", True) in aws_exports.get_named_export_calls


def test_build_raises_when_secret_file_missing():
    with tempfile.TemporaryDirectory() as temp_dir:
        secrets_dir = Path(temp_dir)
        (secrets_dir / "regression_test_app.pem").write_text("regression", encoding="utf-8")
        (secrets_dir / "automerge.pem").write_text("automerge", encoding="utf-8")
        (secrets_dir / "create_pull_request.pem").write_text("create-pr", encoding="utf-8")

        aws_exports = StubAwsExportsService()
        builder = SecretsBuilder(aws_exports=aws_exports, secrets_directory=secrets_dir)

        with pytest.raises(FileNotFoundError):
            builder.build()

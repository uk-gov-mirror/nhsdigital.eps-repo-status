"""Unit tests for AWS CloudFormation export resolution helpers."""

from unittest.mock import MagicMock, call, patch

import pytest

from setup_github_repo.app.aws_exports import AwsExportsService
from setup_github_repo.app.models import Roles


def test_get_named_export_returns_export_value_when_present():
    service = AwsExportsService()
    all_exports = [
        {"Name": "ci-resources:CloudFormationDeployRole", "Value": "deploy-role-arn"},
        {"Name": "ci-resources:CloudFormationCheckVersionRole", "Value": "check-role-arn"},
    ]

    result = service.get_named_export(all_exports, "ci-resources:CloudFormationDeployRole", required=True)

    assert result == "deploy-role-arn"


def test_get_named_export_returns_none_when_optional_export_missing():
    service = AwsExportsService()

    result = service.get_named_export([], "ci-resources:ArtilleryRunnerRole", required=False)

    assert result is None


def test_get_named_export_raises_when_required_export_missing():
    service = AwsExportsService()

    with pytest.raises(ValueError, match="export ci-resources:CloudFormationDeployRole is required but not found"):
        service.get_named_export([], "ci-resources:CloudFormationDeployRole", required=True)


@patch("setup_github_repo.app.aws_exports.boto3.Session")
def test_get_all_exports_fetches_all_pages(mock_session: MagicMock):
    cloudformation_client = MagicMock()
    cloudformation_client.list_exports.side_effect = [
        {
            "Exports": [{"Name": "ExportA", "Value": "ValueA"}],
            "NextToken": "next-token",
        },
        {
            "Exports": [{"Name": "ExportB", "Value": "ValueB"}],
        },
    ]

    session = MagicMock()
    session.client.return_value = cloudformation_client
    mock_session.return_value = session

    service = AwsExportsService()

    result = service.get_all_exports(profile_name="prescription-dev")

    mock_session.assert_called_once_with(profile_name="prescription-dev")
    session.client.assert_called_once_with("cloudformation")
    assert cloudformation_client.list_exports.call_args_list == [
        call(),
        call(NextToken="next-token"),
    ]
    assert result == [
        {"Name": "ExportA", "Value": "ValueA"},
        {"Name": "ExportB", "Value": "ValueB"},
    ]


def test_get_role_exports_maps_required_and_optional_roles():
    service = AwsExportsService()
    all_exports = [
        {"Name": "ci-resources:CloudFormationDeployRole", "Value": "deploy-role-arn"},
        {"Name": "ci-resources:CloudFormationCheckVersionRole", "Value": "check-role-arn"},
        {"Name": "ci-resources:CloudFormationPrepareChangesetRole", "Value": "changeset-role-arn"},
        {"Name": "ci-resources:ReleaseNotesExecuteLambdaRole", "Value": "release-notes-role-arn"},
    ]

    result = service.get_role_exports(all_exports)

    assert result == Roles(
        cloud_formation_deploy_role="deploy-role-arn",
        cloud_formation_check_version_role="check-role-arn",
        cloud_formation_prepare_changeset_role="changeset-role-arn",
        release_notes_execute_lambda_role="release-notes-role-arn",
        artillery_runner_role=None,
    )


def test_get_role_exports_raises_when_required_role_missing():
    service = AwsExportsService()
    all_exports = [
        {"Name": "ci-resources:CloudFormationCheckVersionRole", "Value": "check-role-arn"},
        {"Name": "ci-resources:CloudFormationPrepareChangesetRole", "Value": "changeset-role-arn"},
    ]

    with pytest.raises(ValueError, match="export ci-resources:CloudFormationDeployRole is required but not found"):
        service.get_role_exports(all_exports)

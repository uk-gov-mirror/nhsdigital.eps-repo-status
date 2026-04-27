"""AWS CloudFormation export helpers used to resolve role values by environment."""

from typing import Any

import boto3

from .models import Roles


class AwsExportsService:
    """Load CloudFormation exports and map them to the roles used by repo setup."""

    def get_named_export(self, all_exports: list[dict[str, Any]], export_name: str, required: bool) -> str | None:
        export_value = None

        for export in all_exports:
            if export["Name"] == export_name:
                export_value = export["Value"]
                break

        if required and export_value is None:
            raise ValueError(f"export {export_name} is required but not found")
        return export_value

    def get_all_exports(self, profile_name: str) -> list[dict[str, Any]]:
        print(f"Getting exports for profile {profile_name}")
        session = boto3.Session(profile_name=profile_name)
        cloudformation_client = session.client("cloudformation")

        all_exports: list[dict[str, Any]] = []
        next_token = None

        while True:
            if next_token:
                response = cloudformation_client.list_exports(NextToken=next_token)
            else:
                response = cloudformation_client.list_exports()

            all_exports.extend(response.get("Exports", []))

            next_token = response.get("NextToken")
            if not next_token:
                break
        return all_exports

    def get_role_exports(self, all_exports: list[dict[str, Any]]) -> Roles:
        role_exports = [
            {
                "variable_name": "cloud_formation_deploy_role",
                "export_name": "ci-resources:CloudFormationDeployRole",
                "required": True,
            },
            {
                "variable_name": "cloud_formation_check_version_role",
                "export_name": "ci-resources:CloudFormationCheckVersionRole",
                "required": True,
            },
            {
                "variable_name": "cloud_formation_prepare_changeset_role",
                "export_name": "ci-resources:CloudFormationPrepareChangesetRole",
                "required": True,
            },
            {
                "variable_name": "release_notes_execute_lambda_role",
                "export_name": "ci-resources:ReleaseNotesExecuteLambdaRole",
                "required": False,
            },
            {
                "variable_name": "artillery_runner_role",
                "export_name": "ci-resources:ArtilleryRunnerRole",
                "required": False,
            },
        ]
        all_roles: dict[str, str | None] = {}
        for role_export in role_exports:
            all_roles[role_export["variable_name"]] = self.get_named_export(
                all_exports,
                export_name=role_export["export_name"],
                required=role_export["required"],
            )
        return Roles(**all_roles)

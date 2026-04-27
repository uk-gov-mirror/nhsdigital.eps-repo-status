"""Typed models shared across setup_github_repo services and orchestration."""

from dataclasses import dataclass, field

from github.EnvironmentDeploymentBranchPolicy import EnvironmentDeploymentBranchPolicyParams
from github.EnvironmentProtectionRuleReviewer import ReviewerParams


@dataclass
class Roles:
    cloud_formation_deploy_role: str | None
    cloud_formation_check_version_role: str | None
    cloud_formation_prepare_changeset_role: str | None
    release_notes_execute_lambda_role: str | None
    artillery_runner_role: str | None


@dataclass
class Secrets:
    regression_test_pem: str
    automerge_pem: str
    create_pull_request_pem: str
    eps_multi_repo_deployment_pem: str
    dev_roles: Roles
    int_roles: Roles
    prod_roles: Roles
    qa_roles: Roles
    ref_roles: Roles
    recovery_roles: Roles
    proxygen_prod_role: str
    proxygen_ptl_role: str
    dev_target_spine_server: str
    int_target_spine_server: str
    prod_target_spine_server: str
    qa_target_spine_server: str
    ref_target_spine_server: str
    recovery_target_spine_server: str
    dev_target_service_search_server: str
    int_target_service_search_server: str
    prod_target_service_search_server: str
    qa_target_service_search_server: str
    ref_target_service_search_server: str
    recovery_target_service_search_server: str
    dependabot_token: str | None


@dataclass
class GithubTeams:
    eps_administrator_team: int
    eps_testers_team: int
    eps_team: int
    eps_deployments_team: int


@dataclass
class RepoConfig:
    repoUrl: str
    mainBranch: str
    setTargetSpineServers: bool
    isAccountResources: bool
    setTargetServiceSearchServers: bool
    isEchoRepo: bool
    inWeeklyRelease: bool


@dataclass
class RepoEnvironment:
    name: str
    reviewers: list[ReviewerParams] = field(default_factory=list)
    deployment_branch_policy: EnvironmentDeploymentBranchPolicyParams | None = None

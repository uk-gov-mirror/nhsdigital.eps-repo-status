from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List

from . import Repo
from .github_client import GithubDataClient
from .helpers import (
    DEFAULT_REPOS_FILE,
    load_repos_config,
    write_to_json,
)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate EPS GitHub repository status report.")
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path where the output JSON file will be written.",
    )
    parser.add_argument(
        "-r",
        "--repos-file",
        default=str(DEFAULT_REPOS_FILE),
        help=("Optional path to a JSON file that lists the repositories to process."),
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)
    token = os.getenv("GITHUB_TOKEN", "")
    client = GithubDataClient.from_token(token)
    repos: List[Repo] = load_repos_config(args.repos_file)
    results: List[Dict[str, Any]] = []

    for repo in repos:
        print(f"Processing repository {repo['friendlyName']} from {repo['repoUrl']}...")
        other_prs, dependabot_prs = client.get_pull_requests(repo)
        dependabot_alerts = client.get_dependabot_alerts(repo)
        code_scanning_alerts = client.get_code_scanning_alerts(repo)
        ci_status, ci_url = client.get_workflow_status(repo, repo["ciWorkflow"])
        release_status, release_url = client.get_workflow_status(repo, repo["releaseWorkflow"])
        check_runs, combined_check_runs_status = client.get_latest_status(repo)
        latest_release = client.get_latest_release(repo)
        latest_dev_tag, latest_dev_release_datetime = client.get_latest_environment_tag(repo, "dev")
        latest_qa_tag, latest_qa_release_datetime = client.get_latest_environment_tag(repo, "qa")
        latest_ref_tag, latest_ref_release_datetime = client.get_latest_environment_tag(repo, "ref")
        latest_int_tag, latest_int_release_datetime = client.get_latest_environment_tag(repo, "int")
        latest_prod_tag, latest_prod_release_datetime = client.get_latest_environment_tag(repo, "prod")
        unreleased_tags = client.get_unreleased_tags(repo, latest_prod_tag)
        tool_versions = client.get_tool_versions(repo)
        asdf_version = client.get_asdf_version(repo)

        results.append(
            {
                "repo_url": repo["repoUrl"],
                "friendly_name": repo["friendlyName"],
                "non_dependabot_open_pull_requests": other_prs,
                "dependabot_open_pull_requests": dependabot_prs,
                "critical_dependabot_alerts": dependabot_alerts["CRITICAL"],
                "high_dependabot_alerts": dependabot_alerts["HIGH"],
                "medium_dependabot_alerts": dependabot_alerts["MEDIUM"],
                "low_dependabot_alerts": dependabot_alerts["LOW"],
                "critical_code_scanning_alerts": code_scanning_alerts["CRITICAL"],
                "high_code_scanning_alerts": code_scanning_alerts["HIGH"],
                "medium_code_scanning_alerts": code_scanning_alerts["MEDIUM"],
                "low_code_scanning_alerts": code_scanning_alerts["LOW"],
                "ci_workflow_status": ci_status,
                "ci_workflow_url": ci_url,
                "release_workflow_status": release_status,
                "release_workflow_url": release_url,
                "latest_commit_check_runs": check_runs,
                "latest_commit_combined_check_runs_status": combined_check_runs_status,
                "in_weekly_release": repo["inWeeklyRelease"],
                "latest_release_tag": latest_release["tag"],
                "latest_release_name": latest_release["name"],
                "latest_release_url": latest_release["url"],
                "latest_release_published_at": latest_release["published_at"],
                "latest_prod_tag": latest_prod_tag,
                "latest_prod_release_datetime": latest_prod_release_datetime,
                "latest_dev_tag": latest_dev_tag,
                "latest_dev_release_datetime": latest_dev_release_datetime,
                "latest_qa_tag": latest_qa_tag,
                "latest_qa_release_datetime": latest_qa_release_datetime,
                "latest_ref_tag": latest_ref_tag,
                "latest_ref_release_datetime": latest_ref_release_datetime,
                "latest_int_tag": latest_int_tag,
                "latest_int_release_datetime": latest_int_release_datetime,
                "unreleased_tags": unreleased_tags,
                "tool_version_nodejs": tool_versions.get("nodejs"),
                "tool_version_python": tool_versions.get("python"),
                "tool_version_poetry": tool_versions.get("poetry"),
                "asdf_version": asdf_version,
            }
        )

    write_to_json(args.output, results)


if __name__ == "__main__":
    main()

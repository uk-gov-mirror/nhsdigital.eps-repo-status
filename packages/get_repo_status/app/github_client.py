from __future__ import annotations

import csv
from datetime import datetime
import json
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from github import Auth, Github
from github.GithubException import GithubException

from . import Repo
from .helpers import api_to_html_url, isoformat_no_tz, parse_iso_datetime


class ReleaseEntry(TypedDict, total=False):
    raw: Optional[str]
    parsed: Optional[datetime]


class GithubDataClient:
    def __init__(self, github_client: Github) -> None:
        self.github = github_client

    @classmethod
    def from_token(cls, token: str) -> "GithubDataClient":
        if not token:
            raise EnvironmentError("GITHUB_TOKEN must be set as an environment variable.")
        auth = Auth.Token(token)
        github_client = Github(auth=auth)
        return cls(github_client)

    def get_pull_requests(self, repo: Repo) -> Tuple[int, int]:
        repo_name = repo["repoUrl"]
        gh_repo = self._safe_get_repo(repo_name)
        if gh_repo is None:
            return -1, -1
        try:
            open_prs = gh_repo.get_pulls(state="open")
            dependabot_prs = 0
            other_prs = 0
            for pr in open_prs:
                user_login = getattr(pr.user, "login", None)
                if user_login == "dependabot[bot]":
                    dependabot_prs += 1
                else:
                    other_prs += 1
            return other_prs, dependabot_prs
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error fetching pull requests for {repo_name}: {exc}")
            return -1, -1

    def get_dependabot_alerts(self, repo: Repo) -> Dict[str, int]:
        repo_name = repo["repoUrl"]
        gh_repo = self._safe_get_repo(repo_name)
        if gh_repo is None:
            return {"CRITICAL": -1, "HIGH": -1, "MEDIUM": -1, "LOW": -1}
        try:
            alerts = gh_repo.get_dependabot_alerts(state="open")
            severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for alert in alerts:
                severity = alert.security_vulnerability.severity.upper()
                if severity in severity_counts:
                    severity_counts[severity] += 1
            return severity_counts
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error fetching dependabot alerts for {repo_name}: {exc}")
            return {"CRITICAL": -1, "HIGH": -1, "MEDIUM": -1, "LOW": -1}

    def get_code_scanning_alerts(self, repo: Repo) -> Dict[str, int]:
        repo_name = repo["repoUrl"]
        gh_repo = self._safe_get_repo(repo_name)
        if gh_repo is None:
            return {"CRITICAL": -1, "HIGH": -1, "MEDIUM": -1, "LOW": -1}
        try:
            alerts = gh_repo.get_codescan_alerts()
            severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for alert in alerts:
                severity = getattr(alert.rule, "severity", "").upper()
                if severity in severity_counts:
                    severity_counts[severity] += 1
            return severity_counts
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error fetching code scanning alerts for {repo_name}: {exc}")
            return {"CRITICAL": -1, "HIGH": -1, "MEDIUM": -1, "LOW": -1}

    def get_workflow_status(self, repo: Repo, workflow_name: str) -> Tuple[str, str]:
        if workflow_name == "NONE":
            return "N/A", "N/A"
        repo_name = repo["repoUrl"]
        gh_repo = self._safe_get_repo(repo_name)
        if gh_repo is None:
            return "Error", "Error"
        try:
            workflows = gh_repo.get_workflows()
            for workflow in workflows:
                if workflow.path == f".github/workflows/{workflow_name}":
                    runs = workflow.get_runs()
                    if runs.totalCount > 0:
                        latest_run = runs[0]
                        if latest_run.status == "completed":
                            return latest_run.conclusion, api_to_html_url(latest_run.url)
                        return latest_run.status, api_to_html_url(latest_run.url)
            return "No Runs", "No Runs"
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error fetching workflow status for {repo_name}, workflow {workflow_name}: {exc}")
            return "Error", "Error"

    def get_latest_status(self, repo: Repo) -> Tuple[List[Dict[str, Optional[str]]], str]:
        repo_name = repo["repoUrl"]
        branch_name = repo.get("mainBranch", "main")
        gh_repo = self._safe_get_repo(repo_name)
        if gh_repo is None:
            return [], "unknown"
        try:
            branch = gh_repo.get_branch(branch_name)
            commit = branch.commit
            check_suites = commit.get_check_suites()
            statuses = commit.get_statuses()
            check_run_entries: List[Dict[str, Optional[str]]] = []
            combined_check_runs_status = "success"
            for check_suite in check_suites:
                if check_suite.head_branch != repo.get("mainBranch"):
                    continue
                check_runs = check_suite.get_check_runs()
                for check_run in check_runs:
                    if check_run.name == "Dependabot":
                        continue
                    check_run_entries.append(
                        {
                            "name": check_run.name,
                            "html_url": check_run.html_url,
                            "status_url": check_run.html_url,
                            "status": check_run.status,
                            "conclusion": check_run.conclusion,
                        }
                    )
                    if check_run.status == "completed" and check_run.conclusion in {
                        "failure",
                        "cancelled",
                        "timed_out",
                    }:
                        combined_check_runs_status = "failure"
            for status in statuses:
                check_run_entries.append(
                    {
                        "name": status.context,
                        "html_url": status.target_url,
                        "status_url": status.target_url,
                        "status": status.state,
                        "conclusion": status.state,
                    }
                )
                if status.state in {"failure", "error"}:
                    combined_check_runs_status = "failure"
            return check_run_entries, combined_check_runs_status
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error fetching combined status for {repo_name}: {exc}")
            return [], "unknown"

    def get_latest_release(self, repo: Repo) -> Dict[str, Optional[str]]:
        repo_name = repo["repoUrl"]
        gh_repo = self._safe_get_repo(repo_name)
        if gh_repo is None:
            return {"tag": None, "name": None, "url": None, "published_at": None}
        try:
            release = gh_repo.get_latest_release()
            published_at = isoformat_no_tz(release.published_at)
            return {
                "tag": release.tag_name,
                "name": release.name,
                "url": release.html_url,
                "published_at": published_at,
            }
        except GithubException as exc:
            if exc.status != 404:
                print(f"Error fetching latest release for {repo_name}: {exc}")
            return {"tag": None, "name": None, "url": None, "published_at": None}
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error fetching latest release for {repo_name}: {exc}")
            return {"tag": None, "name": None, "url": None, "published_at": None}

    def get_commits_since_last_release(self, repo: Repo) -> int:
        repo_name = repo["repoUrl"]
        branch_name = repo.get("mainBranch", "main")
        gh_repo = self._safe_get_repo(repo_name)
        if gh_repo is None:
            return -1
        try:
            release = gh_repo.get_latest_release()
            tag_name = getattr(release, "tag_name", None)
            if not tag_name:
                return -1
            comparison = gh_repo.compare(tag_name, branch_name)
            ahead_by = getattr(comparison, "ahead_by", None)
            if ahead_by is None:
                return -1
            return int(ahead_by)
        except GithubException as exc:
            if exc.status != 404:
                print(f"Error fetching commits since last release for {repo_name}: {exc}")
            return -1
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error fetching commits since last release for {repo_name}: {exc}")
            return -1

    def get_tool_versions(self, repo: Repo) -> Dict[str, Optional[str]]:
        repo_name = repo["repoUrl"]
        ref = repo.get("mainBranch", "main")
        content = self.get_text_file_from_repo(repo_name, ".tool-versions", ref)
        versions: Dict[str, Optional[str]] = {"nodejs": None, "python": None, "poetry": None}
        if not content:
            return versions
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 2:
                continue
            tool, version = parts[0], parts[1]
            if tool in versions and versions[tool] is None:
                versions[tool] = version
        return versions

    def get_asdf_version(self, repo: Repo) -> Optional[str]:
        repo_name = repo["repoUrl"]
        ref = repo.get("mainBranch", "main")
        content = self.get_text_file_from_repo(repo_name, ".tool-versions.asdf", ref)
        if not content:
            return None
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            return stripped
        return None

    def get_devcontainer_details(self, repo: Repo) -> Dict[str, str]:
        repo_name = repo["repoUrl"]
        ref = repo.get("mainBranch", "main")
        content = self.get_text_file_from_repo(repo_name, ".devcontainer/devcontainer.json", ref)
        if not content:
            return {"IMAGE_NAME": "n/a", "IMAGE_VERSION": "n/a"}
        try:
            parsed = json.loads(content)
        except Exception:  # pylint: disable=broad-except
            return {"IMAGE_NAME": "n/a", "IMAGE_VERSION": "n/a"}
        build = parsed.get("build") if isinstance(parsed, dict) else None
        args = build.get("args") if isinstance(build, dict) else None
        image_name = args.get("IMAGE_NAME") if isinstance(args, dict) else None
        image_version = args.get("IMAGE_VERSION") if isinstance(args, dict) else None
        return {
            "IMAGE_NAME": image_name or "n/a",
            "IMAGE_VERSION": image_version or "n/a",
        }

    def get_latest_environment_tag(  # noqa: C901
        self, repo: Repo, environment: str
    ) -> Tuple[Optional[str], Optional[str]]:
        repo_name = repo["repoUrl"]
        release_suffixes = repo.get("releaseFiles") or []
        if not release_suffixes:
            return None, None

        gh_repo = self._safe_get_repo(repo_name)
        if gh_repo is None:
            return None, None

        tags: List[str] = []
        release_entries: List[ReleaseEntry] = []
        is_api_repo = bool(repo.get("isApiRepo", False))
        is_spine_repo = bool(repo.get("isSpineRepo", False))

        for suffix in release_suffixes:
            resolved_environment = environment
            if is_api_repo and environment in ["dev", "qa"]:
                resolved_environment = f"internal-{environment}"
            if is_spine_repo and environment in ["prod"]:
                resolved_environment = "live"
            file_name = f"{resolved_environment}{suffix}"
            entry = self._load_release_entry(gh_repo, repo_name, file_name)
            if entry is None:
                return None, None
            prod_tag, release_entry = entry
            tags.append(prod_tag)
            release_entries.append(release_entry)

        unique_tags = {tag for tag in tags if tag}
        if not unique_tags:
            return None, None
        if len(unique_tags) > 1:
            return "Inconsistent released tags", None
        agreed_tag = next(iter(unique_tags))

        latest_entry: Optional[ReleaseEntry] = None
        latest_time: Optional[datetime] = None
        for entry in release_entries:
            parsed = entry.get("parsed")
            if parsed is None:
                continue
            if latest_time is None or parsed > latest_time:
                latest_entry = entry
                latest_time = parsed
        if latest_entry:
            return agreed_tag, latest_entry.get("raw")
        for entry in release_entries:
            if entry.get("raw"):
                return agreed_tag, entry["raw"]
        return agreed_tag, None

    def get_unreleased_tags(self, repo: Repo, latest_prod_tag: Optional[str]) -> List[str]:
        repo_name = repo["repoUrl"]
        if not latest_prod_tag or latest_prod_tag == "Inconsistent released tags":
            return []
        gh_repo = self._safe_get_repo(repo_name)
        if gh_repo is None:
            return []
        try:
            releases = gh_repo.get_releases()
            unreleased: List[str] = []
            for release in releases:
                if release.tag_name == latest_prod_tag:
                    return unreleased
                unreleased.append(release.tag_name)
            return []
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error fetching releases for {repo_name}: {exc}")
            return []

    def get_text_file_from_repo(self, repo_name: str, path: str, ref: str) -> Optional[str]:
        gh_repo = self._safe_get_repo(repo_name)
        if gh_repo is None:
            return None
        try:
            content_file = gh_repo.get_contents(path, ref=ref)
            return content_file.decoded_content.decode("utf-8")
        except GithubException as exc:
            if exc.status != 404:
                print(f"Error fetching {path} for {repo_name}: {exc}")
            return None
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error fetching {path} for {repo_name}: {exc}")
            return None

    def _safe_get_repo(self, repo_name: str) -> Optional[Any]:
        try:
            return self.github.get_repo(repo_name)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error loading repository {repo_name}: {exc}")
            return None

    def _read_release_file_first_row(
        self, gh_repo: Any, repo_name: str, file_name: str
    ) -> Optional[Dict[str, Optional[str]]]:
        path = f"_data/{file_name}"
        try:
            content = gh_repo.get_contents(path, ref="gh-pages")
        except GithubException as exc:
            if exc.status != 404:
                print(f"Error fetching {path} for {repo_name}: {exc}")
            return None
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error fetching {path} for {repo_name}: {exc}")
            return None
        try:
            decoded = content.decoded_content.decode("utf-8")
            reader = csv.DictReader(decoded.splitlines())
            return next(reader, None)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error parsing {path} for {repo_name}: {exc}")
            return None

    def _load_release_entry(self, gh_repo: Any, repo_name: str, file_name: str) -> Optional[Tuple[str, ReleaseEntry]]:
        first_row = self._read_release_file_first_row(gh_repo, repo_name, file_name)
        if not first_row:
            return None
        prod_tag_raw = first_row.get("tag") or ""
        prod_tag = prod_tag_raw.strip()
        if not prod_tag:
            return None
        release_raw_value = first_row.get("release_datetime") or ""
        release_raw = release_raw_value.strip() or None
        release_entry: ReleaseEntry = {
            "raw": release_raw,
            "parsed": parse_iso_datetime(release_raw),
        }
        return prod_tag, release_entry

"""Repository status parsing and loading utilities for eps-repo-status data."""

import json
from pathlib import Path
from typing import Any

from .models import RepoConfig


def _as_bool(entry: dict[str, Any], camel_key: str, snake_key: str, default: bool = False) -> bool:
    value = entry.get(camel_key)
    if value is None:
        value = entry.get(snake_key)
    if value is None:
        return default
    return bool(value)


def _normalise_repo_entry(entry: Any, fallback_repo_url: str | None = None) -> RepoConfig:
    if isinstance(entry, str):
        repo_url = entry
        entry_dict: dict[str, Any] = {}
    elif isinstance(entry, dict):
        entry_dict = dict(entry)
        repo_url = entry_dict.get("repoUrl") or entry_dict.get("repo") or fallback_repo_url
    else:
        raise ValueError("Unsupported repo entry type in repos.json")

    if not repo_url:
        raise ValueError("Repo entry missing repoUrl")

    repo_url = repo_url.strip()
    if not repo_url:
        raise ValueError("Repo entry contains empty repoUrl")

    return RepoConfig(
        repoUrl=repo_url,
        mainBranch=str(entry_dict.get("mainBranch") or entry_dict.get("main_branch") or "main"),
        setTargetSpineServers=_as_bool(
            entry_dict,
            camel_key="setTargetSpineServers",
            snake_key="set_target_spine_servers",
        ),
        isAccountResources=_as_bool(
            entry_dict,
            camel_key="isAccountResources",
            snake_key="is_account_resources",
        ),
        setTargetServiceSearchServers=_as_bool(
            entry_dict,
            camel_key="setTargetServiceSearchServers",
            snake_key="set_target_service_search_servers",
        ),
        isEchoRepo=_as_bool(
            entry_dict,
            camel_key="isEchoRepo",
            snake_key="is_echo_repo",
        ),
        inWeeklyRelease=_as_bool(
            entry_dict,
            camel_key="inWeeklyRelease",
            snake_key="in_weekly_release",
        ),
    )


def _parse_repos_payload(payload: Any) -> list[RepoConfig]:
    if isinstance(payload, list):
        return [_normalise_repo_entry(entry) for entry in payload]
    if isinstance(payload, dict):
        repos_section = payload.get("repos")
        if isinstance(repos_section, list):
            return [_normalise_repo_entry(entry) for entry in repos_section]
        if isinstance(repos_section, dict):
            return [_normalise_repo_entry(entry, fallback_repo_url=key) for key, entry in repos_section.items()]
    raise ValueError("repos.json must contain either a list of repos or a 'repos' section")


class RepoStatusLoader:
    """Load repository setup configuration from the local repos.json file."""

    def load_repo_configs(self) -> list[RepoConfig]:
        repos_path = Path(__file__).resolve().parents[3] / "repos.json"
        print(f"Loading repo configuration from local file: {repos_path}")
        payload = json.loads(repos_path.read_text(encoding="utf-8"))
        return _parse_repos_payload(payload)

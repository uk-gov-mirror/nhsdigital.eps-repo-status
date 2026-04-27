"""Unit tests for repo status payload normalization, parsing, and loading."""

import importlib
import json
from pathlib import Path

import pytest

repo_status = importlib.import_module("setup_github_repo.app.repo_status")
RepoStatusLoader = repo_status.RepoStatusLoader


def test_parse_repos_payload_from_list_of_strings():
    payload = ["NHSDigital/repo-one", "NHSDigital/repo-two"]

    result = repo_status._parse_repos_payload(payload)

    assert len(result) == 2
    assert result[0].repoUrl == "NHSDigital/repo-one"
    assert result[0].mainBranch == "main"
    assert result[0].setTargetSpineServers is False
    assert result[0].isAccountResources is False
    assert result[0].setTargetServiceSearchServers is False
    assert result[0].isEchoRepo is False
    assert result[0].inWeeklyRelease is False


def test_parse_repos_payload_from_repos_dict():
    payload = {
        "repos": {
            "NHSDigital/repo-one": {
                "mainBranch": "release/1.x",
                "set_target_spine_servers": True,
                "is_account_resources": True,
                "set_target_service_search_servers": False,
                "is_echo_repo": True,
                "in_weekly_release": True,
            }
        }
    }

    result = repo_status._parse_repos_payload(payload)

    assert len(result) == 1
    assert result[0].repoUrl == "NHSDigital/repo-one"
    assert result[0].mainBranch == "release/1.x"
    assert result[0].setTargetSpineServers is True
    assert result[0].isAccountResources is True
    assert result[0].setTargetServiceSearchServers is False
    assert result[0].isEchoRepo is True
    assert result[0].inWeeklyRelease is True


def test_normalise_repo_entry_rejects_empty_repo_url():
    with pytest.raises(ValueError):
        repo_status._normalise_repo_entry({"repoUrl": "   "})


def test_parse_repos_payload_rejects_invalid_shape():
    with pytest.raises(ValueError):
        repo_status._parse_repos_payload({"notRepos": []})


def test_load_repo_configs_from_local_repos_file():
    payload = {
        "repos": [
            {
                "repoUrl": "NHSDigital/repo-one",
                "mainBranch": "main",
                "setTargetSpineServers": True,
                "isAccountResources": False,
                "setTargetServiceSearchServers": True,
                "isEchoRepo": False,
                "inWeeklyRelease": True,
            }
        ]
    }
    root_repos_file = Path(__file__).resolve().parents[3] / "repos.json"
    original_content = root_repos_file.read_text(encoding="utf-8")
    root_repos_file.write_text(json.dumps(payload), encoding="utf-8")

    loader = RepoStatusLoader()

    try:
        result = loader.load_repo_configs()
    finally:
        root_repos_file.write_text(original_content, encoding="utf-8")

    assert result[0].repoUrl == "NHSDigital/repo-one"
    assert result[0].mainBranch == "main"
    assert result[0].setTargetSpineServers is True
    assert result[0].setTargetServiceSearchServers is True
    assert result[0].inWeeklyRelease is True

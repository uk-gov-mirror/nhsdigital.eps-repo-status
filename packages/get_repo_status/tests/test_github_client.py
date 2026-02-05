from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from github.GithubException import GithubException

from app.github_client import GithubDataClient


@pytest.fixture
def github_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(github_client: MagicMock) -> GithubDataClient:
    return GithubDataClient(github_client)


@pytest.fixture
def repo_factory():
    def _factory(**overrides):
        base = {"repoUrl": "owner/name", "mainBranch": "main", "isApiRepo": False}
        base.update(overrides)
        return base

    return _factory


def make_github_exception(status: int = 500) -> GithubException:
    return GithubException(status, {"message": "boom"})


def test_get_pull_requests_counts_dependabot_and_other_prs(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_pulls.return_value = [
        SimpleNamespace(user=SimpleNamespace(login="dependabot[bot]")),
        SimpleNamespace(user=SimpleNamespace(login="alice")),
        SimpleNamespace(user=SimpleNamespace(login=None)),
    ]
    github_client.get_repo.return_value = gh_repo

    result = client.get_pull_requests(repo_factory())

    assert result == (2, 1)


def test_get_pull_requests_returns_error_tuple_on_exception(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    github_client.get_repo.side_effect = Exception("boom")

    result = client.get_pull_requests(repo_factory())

    assert result == (-1, -1)


def test_get_dependabot_alerts_counts_by_severity(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_dependabot_alerts.return_value = [
        SimpleNamespace(security_vulnerability=SimpleNamespace(severity="critical")),
        SimpleNamespace(security_vulnerability=SimpleNamespace(severity="HIGH")),
        SimpleNamespace(security_vulnerability=SimpleNamespace(severity="unknown")),
    ]
    github_client.get_repo.return_value = gh_repo

    result = client.get_dependabot_alerts(repo_factory())

    assert result == {"CRITICAL": 1, "HIGH": 1, "MEDIUM": 0, "LOW": 0}


def test_get_dependabot_alerts_returns_error_counts_on_exception(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    github_client.get_repo.side_effect = Exception("boom")

    result = client.get_dependabot_alerts(repo_factory())

    assert result == {"CRITICAL": -1, "HIGH": -1, "MEDIUM": -1, "LOW": -1}


def test_get_code_scanning_alerts_returns_error_counts_on_exception(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    github_client.get_repo.side_effect = Exception("boom")

    result = client.get_code_scanning_alerts(repo_factory())

    assert result == {"CRITICAL": -1, "HIGH": -1, "MEDIUM": -1, "LOW": -1}


class FakeRuns(list):
    def __init__(self, items):
        super().__init__(items)
        self.totalCount = len(items)


def test_get_workflow_status_returns_latest_conclusion(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    latest_run = SimpleNamespace(
        status="completed",
        conclusion="success",
        url="https://api.github.com/repos/owner/name/actions/runs/1",
    )
    workflow = MagicMock()
    workflow.path = ".github/workflows/ci.yml"
    workflow.get_runs.return_value = FakeRuns([latest_run])
    gh_repo.get_workflows.return_value = [workflow]
    github_client.get_repo.return_value = gh_repo

    status, url = client.get_workflow_status(repo_factory(), "ci.yml")

    assert status == "success"
    assert url == "https://github.com/owner/name/actions/runs/1"


def test_get_workflow_status_returns_error_on_exception(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    github_client.get_repo.side_effect = Exception("boom")

    status, url = client.get_workflow_status(repo_factory(), "ci.yml")

    assert status == "Error"
    assert url == "Error"


def test_get_latest_status_combines_check_runs_and_statuses(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    branch = SimpleNamespace()
    commit = MagicMock()
    commit.get_check_runs.return_value = [
        SimpleNamespace(
            name="Build",
            html_url="https://example.com/build",
            status="completed",
            conclusion="failure",
        ),
        SimpleNamespace(name="Dependabot", html_url="", status="completed", conclusion="success"),
    ]
    commit.get_statuses.return_value = [
        SimpleNamespace(context="ci/lint", target_url="https://example.com/lint", state="failure"),
    ]
    branch.commit = commit
    gh_repo.get_branch.return_value = branch
    github_client.get_repo.return_value = gh_repo

    entries, overall = client.get_latest_status(repo_factory())

    assert overall == "failure"
    assert len(entries) == 2
    assert entries[0]["name"] == "Build"
    assert entries[1]["name"] == "ci/lint"


def test_get_latest_status_returns_unknown_on_exception(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    github_client.get_repo.side_effect = Exception("boom")

    entries, overall = client.get_latest_status(repo_factory())

    assert entries == []
    assert overall == "unknown"


def test_get_latest_release_returns_release_info(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_latest_release.return_value = SimpleNamespace(
        tag_name="v1.0.0",
        name="Release",
        html_url="https://github.com/owner/name/releases/tag/v1.0.0",
        published_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
    github_client.get_repo.return_value = gh_repo

    release = client.get_latest_release(repo_factory())

    assert release == {
        "tag": "v1.0.0",
        "name": "Release",
        "url": "https://github.com/owner/name/releases/tag/v1.0.0",
        "published_at": "2023-01-01T00:00:00",
    }


def test_get_latest_release_returns_none_fields_on_exception(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_latest_release.side_effect = Exception("boom")
    github_client.get_repo.return_value = gh_repo

    release = client.get_latest_release(repo_factory())

    assert release == {"tag": None, "name": None, "url": None, "published_at": None}


def test_get_latest_release_returns_none_fields_on_github_404(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_latest_release.side_effect = make_github_exception(404)
    github_client.get_repo.return_value = gh_repo

    release = client.get_latest_release(repo_factory())

    assert release == {"tag": None, "name": None, "url": None, "published_at": None}


def test_get_commits_since_last_release_returns_ahead_count(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_latest_release.return_value = SimpleNamespace(tag_name="v1.0.0")
    gh_repo.compare.return_value = SimpleNamespace(ahead_by=4)
    github_client.get_repo.return_value = gh_repo

    count = client.get_commits_since_last_release(repo_factory())

    assert count == 4
    gh_repo.compare.assert_called_once_with("v1.0.0", "main")


def test_get_commits_since_last_release_returns_negative_on_missing_release(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_latest_release.side_effect = make_github_exception(404)
    github_client.get_repo.return_value = gh_repo

    count = client.get_commits_since_last_release(repo_factory())

    assert count == -1


def test_get_tool_versions_parses_known_tools(client: GithubDataClient, repo_factory) -> None:
    client.get_text_file_from_repo = MagicMock(
        return_value="""nodejs 18.16.0\npython 3.11.1\npoetry 1.5.1\nnodejs 20.0.0\n"""
    )

    versions = client.get_tool_versions(repo_factory())

    assert versions == {"nodejs": "18.16.0", "python": "3.11.1", "poetry": "1.5.1"}


def test_get_asdf_version_returns_first_non_comment_line(client: GithubDataClient, repo_factory) -> None:
    client.get_text_file_from_repo = MagicMock(return_value="""   \n# comment\n0.12.3\n""")

    version = client.get_asdf_version(repo_factory())

    assert version == "0.12.3"


def test_get_latest_environment_tag_returns_latest_release_datetime(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    content_map = {
        "_data/prod.csv": "tag,release_datetime\nv1.2.3,2024-01-10T09:00:00Z\n",
        "_data/prod_extra.csv": "tag,release_datetime\nv1.2.3,2024-01-12T09:00:00Z\n",
    }

    def _get_contents(path, ref):
        assert ref == "gh-pages"
        return SimpleNamespace(decoded_content=content_map[path].encode("utf-8"))

    gh_repo.get_contents.side_effect = _get_contents
    github_client.get_repo.return_value = gh_repo

    tag, released_at = client.get_latest_environment_tag(
        repo_factory(releaseFiles=[".csv", "_extra.csv"]),
        "prod",
    )

    assert tag == "v1.2.3"
    assert released_at == "2024-01-12T09:00:00Z"


def test_get_latest_environment_tag_uses_internal_prefix_for_api_repo(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    content_map = {
        "_data/internal-dev.csv": "tag,release_datetime\nv1.2.3,2024-01-10T09:00:00Z\n",
    }

    def _get_contents(path, ref):
        assert ref == "gh-pages"
        return SimpleNamespace(decoded_content=content_map[path].encode("utf-8"))

    gh_repo.get_contents.side_effect = _get_contents
    github_client.get_repo.return_value = gh_repo

    tag, released_at = client.get_latest_environment_tag(
        repo_factory(releaseFiles=[".csv"], isApiRepo=True),
        "dev",
    )

    assert tag == "v1.2.3"
    assert released_at == "2024-01-10T09:00:00Z"


def test_get_latest_environment_tag_detects_inconsistent_tags(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    content_map = {
        "_data/prod_first.csv": "tag,release_datetime\nv1.2.3,2024-01-10T09:00:00Z\n",
        "_data/prod_second.csv": "tag,release_datetime\nv2.0.0,2024-01-11T11:00:00Z\n",
    }

    def _get_contents(path, ref):
        assert ref == "gh-pages"
        return SimpleNamespace(decoded_content=content_map[path].encode("utf-8"))

    gh_repo.get_contents.side_effect = _get_contents
    github_client.get_repo.return_value = gh_repo

    tag, released_at = client.get_latest_environment_tag(
        repo_factory(releaseFiles=["_first.csv", "_second.csv"]),
        "prod",
    )

    assert tag == "Inconsistent released tags"
    assert released_at is None


def test_get_latest_environment_tag_returns_none_when_repo_load_fails(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    github_client.get_repo.side_effect = Exception("boom")

    tag, released_at = client.get_latest_environment_tag(
        repo_factory(releaseFiles=[".csv"]),
        "prod",
    )

    assert tag is None
    assert released_at is None


def test_get_latest_environment_tag_returns_none_when_file_fetch_fails(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_contents.side_effect = make_github_exception(500)
    github_client.get_repo.return_value = gh_repo

    tag, released_at = client.get_latest_environment_tag(
        repo_factory(releaseFiles=[".csv"]),
        "prod",
    )

    assert tag is None
    assert released_at is None


def test_get_latest_environment_tag_returns_none_when_file_is_empty(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_contents.return_value = SimpleNamespace(decoded_content="tag,release_datetime\n".encode("utf-8"))
    github_client.get_repo.return_value = gh_repo

    tag, released_at = client.get_latest_environment_tag(
        repo_factory(releaseFiles=[".csv"]),
        "prod",
    )

    assert tag is None
    assert released_at is None


def test_get_latest_environment_tag_returns_none_when_tag_missing(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_contents.return_value = SimpleNamespace(
        decoded_content="tag,release_datetime\n,2024-01-10T09:00:00Z\n".encode("utf-8")
    )
    github_client.get_repo.return_value = gh_repo

    tag, released_at = client.get_latest_environment_tag(
        repo_factory(releaseFiles=[".csv"]),
        "prod",
    )

    assert tag is None
    assert released_at is None


def test_get_latest_environment_tag_uses_correct_name_for_spine_repo(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    content_map = {
        "_data/live.csv": "tag,release_datetime\nv1.2.3,2024-01-10T09:00:00Z\n",
    }

    def _get_contents(path, ref):
        assert ref == "gh-pages"
        return SimpleNamespace(decoded_content=content_map[path].encode("utf-8"))

    gh_repo.get_contents.side_effect = _get_contents
    github_client.get_repo.return_value = gh_repo

    tag, released_at = client.get_latest_environment_tag(
        repo_factory(releaseFiles=[".csv"], isSpineRepo=True),
        "prod",
    )

    assert tag == "v1.2.3"
    assert released_at == "2024-01-10T09:00:00Z"


def test_get_unreleased_tags_returns_expected_order(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_releases.return_value = [
        SimpleNamespace(tag_name="v3.0.0"),
        SimpleNamespace(tag_name="v2.1.0"),
        SimpleNamespace(tag_name="v2.0.0"),
    ]
    github_client.get_repo.return_value = gh_repo

    unreleased = client.get_unreleased_tags(repo_factory(), "v2.1.0")

    assert unreleased == ["v3.0.0"]


def test_get_unreleased_tags_returns_empty_on_exception(
    client: GithubDataClient, github_client: MagicMock, repo_factory
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_releases.side_effect = Exception("boom")
    github_client.get_repo.return_value = gh_repo

    unreleased = client.get_unreleased_tags(repo_factory(), "v2.1.0")

    assert unreleased == []


def test_get_text_file_from_repo_returns_none_on_github_exception(
    client: GithubDataClient, github_client: MagicMock
) -> None:
    gh_repo = MagicMock()
    gh_repo.get_contents.side_effect = make_github_exception(500)
    github_client.get_repo.return_value = gh_repo

    result = client.get_text_file_from_repo("owner/name", ".tool-versions", "main")

    assert result is None


def test_get_text_file_from_repo_returns_none_on_404(client: GithubDataClient, github_client: MagicMock) -> None:
    gh_repo = MagicMock()
    gh_repo.get_contents.side_effect = make_github_exception(404)
    github_client.get_repo.return_value = gh_repo

    result = client.get_text_file_from_repo("owner/name", ".tool-versions", "main")

    assert result is None

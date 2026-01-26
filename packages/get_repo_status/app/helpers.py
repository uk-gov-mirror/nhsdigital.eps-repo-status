from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from . import Repo

DEFAULT_REPOS_FILE = Path(__file__).with_name("repos.json")


def isoformat_no_tz(dt: Optional[datetime]) -> Optional[str]:
    """Return ISO string without timezone information."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    dt = dt.replace(tzinfo=None)
    return dt.isoformat()


def api_to_html_url(url: str) -> str:
    api_prefix = "https://api.github.com/repos/"
    html_prefix = "https://github.com/"
    if url.startswith(api_prefix):
        return url.replace(api_prefix, html_prefix, 1)
    return url


def load_repos_config(repo_file: Union[str, Path, None] = None) -> List[Repo]:
    resolved = Path(repo_file) if repo_file else DEFAULT_REPOS_FILE
    if not resolved.exists():
        raise FileNotFoundError(f"Repository list not found: {resolved}")
    with resolved.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Repository list must be a JSON array")
    return data


def write_to_json(output_path: Union[str, Path], data: List[Dict[str, Any]]) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_date_time": isoformat_no_tz(datetime.now(timezone.utc).replace(microsecond=0)),
        "repos": data,
    }
    with output.open("w", encoding="utf-8") as jsonfile:
        json.dump(payload, jsonfile, indent=2)


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        normalized = value.strip().replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None

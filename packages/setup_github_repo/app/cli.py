"""CLI entrypoint that validates auth prerequisites and runs repository setup."""

import argparse
import subprocess

from .constants import AWS_PROFILE_BY_ENV
from .runner import SetupGithubRepoRunner


def _read_gh_auth_token() -> str | None:
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("GitHub CLI (gh) is not installed or not available on PATH.") from exc

    if result.returncode != 0:
        return None

    token = result.stdout.strip()
    if not token:
        return None
    return token


def _get_or_create_gh_auth_token() -> str:
    existing_token = _read_gh_auth_token()
    if existing_token:
        return existing_token

    print("No GitHub token found. Running gh auth login to obtain one...")
    subprocess.run(["gh", "auth", "login"], check=True)

    token_after_login = _read_gh_auth_token()
    if token_after_login:
        return token_after_login

    raise RuntimeError("Unable to retrieve GitHub token after running 'gh auth login'.")


def resolve_gh_auth_token(explicit_token: str | None) -> str:
    if explicit_token:
        return explicit_token
    return _get_or_create_gh_auth_token()


def _has_valid_aws_credentials_for_profile(profile_name: str) -> bool:
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity", "--profile", profile_name],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("AWS CLI (aws) is not installed or not available on PATH.") from exc

    return result.returncode == 0


def _get_invalid_aws_profiles() -> list[str]:
    required_profiles = sorted(set(AWS_PROFILE_BY_ENV.values()))
    return [
        profile_name for profile_name in required_profiles if not _has_valid_aws_credentials_for_profile(profile_name)
    ]


def ensure_aws_credentials() -> None:
    invalid_profiles = _get_invalid_aws_profiles()
    if not invalid_profiles:
        return

    invalid_profiles_text = ", ".join(invalid_profiles)
    print(
        f"AWS credentials missing or expired for profiles: {invalid_profiles_text}. "
        "Running make aws-login to refresh credentials..."
    )
    try:
        subprocess.run(["make", "aws-login"], check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("make is not installed or not available on PATH.") from exc

    remaining_invalid_profiles = _get_invalid_aws_profiles()
    if remaining_invalid_profiles:
        remaining_profiles_text = ", ".join(remaining_invalid_profiles)
        raise RuntimeError(
            "AWS credentials are still missing or expired after running make aws-login for profiles: "
            f"{remaining_profiles_text}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gh_auth_token",
        required=False,
        help=(
            "Please provide a github auth token. If authenticated with github cli this can be "
            "retrieved using 'gh auth token'. If omitted, this script will try to retrieve one automatically."
        ),
    )

    arguments = parser.parse_args()
    ensure_aws_credentials()
    github_auth_token = resolve_gh_auth_token(arguments.gh_auth_token)
    runner = SetupGithubRepoRunner(gh_auth_token=github_auth_token)
    runner.run()

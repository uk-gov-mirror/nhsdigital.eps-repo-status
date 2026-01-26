#!/usr/bin/env python3
"""Wrapper script for running the EPS repo status CLI via poetry."""

import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_MODULE = "packages.get_repo_status.app.cli"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute the EPS repo status exporter without worrying about PYTHONPATH issues."
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to the JSON file that will receive the export.",
    )
    parser.add_argument(
        "-r",
        "--repos-file",
        help="Optional path to a repos config JSON file (defaults to the built-in list).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cmd = [
        "poetry",
        "run",
        "python",
        "-m",
        CLI_MODULE,
        "--output",
        args.output,
    ]
    if args.repos_file:
        cmd.extend(["--repos-file", args.repos_file])

    # Running via module ensures the relative imports inside cli.py resolve correctly.
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


if __name__ == "__main__":
    main()

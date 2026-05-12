# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 ProtocolWarden
"""PlatformDeployment stack management CLI."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .config import load_config
from .health import check_all_health
from .lane_cli import cmd_lane_doctor, cmd_lane_health, cmd_lane_start, cmd_lane_status, cmd_lane_stop
from .status import aggregate_status


_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]
_COMPOSE_FILE = _REPO_ROOT / "compose" / "docker-compose.yml"
_CONFIG_DIR = _REPO_ROOT / "config" / "platformdeployment"
_ENV_FILE = _REPO_ROOT / ".env"


def _compose(*args: str) -> int:
    cmd = [
        "docker", "compose",
        "--file", str(_COMPOSE_FILE),
    ]
    if _ENV_FILE.exists():
        cmd += ["--env-file", str(_ENV_FILE)]
    cmd += list(args)
    result = subprocess.run(cmd, timeout=86400)
    return result.returncode


def _load_or_die() -> dict:
    endpoints_file = _CONFIG_DIR / "endpoints.yaml"
    if not endpoints_file.exists():
        sys.exit(1)
    try:
        cfg = load_config(_CONFIG_DIR)
    except Exception:
        sys.exit(1)
    return cfg.services


def cmd_up(args: argparse.Namespace) -> int:
    return _compose("up", "--detach", "--remove-orphans")


def cmd_down(args: argparse.Namespace) -> int:
    return _compose("down", "--remove-orphans")


def cmd_health(args: argparse.Namespace) -> int:
    services = _load_or_die()
    results = check_all_health(services)
    if args.json:
        all_ok = all(r["healthy"] for r in results.values())
        return 0 if all_ok else 1
    return 0 if all(result["healthy"] for result in results.values()) else 1


def cmd_status(args: argparse.Namespace) -> int:
    services = _load_or_die()
    summary = aggregate_status(services)
    if args.json:
        return 0 if summary.get("status") == "healthy" else 1
    return 0 if summary.get("status") == "healthy" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="platform_deployment_cli",
        description="PlatformDeployment stack management CLI.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p_up = sub.add_parser("up", help="Start the stack in detached mode.")
    p_up.set_defaults(func=cmd_up)

    p_down = sub.add_parser("down", help="Stop and remove stack containers.")
    p_down.set_defaults(func=cmd_down)

    p_health = sub.add_parser("health", help="Check health endpoints.")
    p_health.add_argument("--json", action="store_true", help="Output results as JSON.")
    p_health.set_defaults(func=cmd_health)

    p_status = sub.add_parser("status", help="Print aggregate status summary.")
    p_status.add_argument("--json", action="store_true", help="Output status as JSON.")
    p_status.set_defaults(func=cmd_status)

    p_lane = sub.add_parser("lane", help="Manage the aider_local execution lane.")
    lane_sub = p_lane.add_subparsers(dest="lane_action", metavar="<action>")

    p_lane_start = lane_sub.add_parser("start", help="Start local model services.")
    p_lane_start.add_argument("lane_name", nargs="?", default="aider_local")
    p_lane_start.set_defaults(func=cmd_lane_start)

    p_lane_stop = lane_sub.add_parser("stop", help="Stop local model services.")
    p_lane_stop.add_argument("lane_name", nargs="?", default="aider_local")
    p_lane_stop.set_defaults(func=cmd_lane_stop)

    p_lane_status = lane_sub.add_parser("status", help="Show lane state and model health.")
    p_lane_status.add_argument("lane_name", nargs="?", default="aider_local")
    p_lane_status.add_argument("--json", action="store_true", help="Output as JSON.")
    p_lane_status.set_defaults(func=cmd_lane_status)

    p_lane_health = lane_sub.add_parser("health", help="Run a live health check.")
    p_lane_health.add_argument("lane_name", nargs="?", default="aider_local")
    p_lane_health.add_argument("--json", action="store_true", help="Output as JSON.")
    p_lane_health.set_defaults(func=cmd_lane_health)

    p_lane_doctor = lane_sub.add_parser("doctor", help="Full pre-flight check for the lane.")
    p_lane_doctor.add_argument("lane_name", nargs="?", default="aider_local")
    p_lane_doctor.add_argument("--json", action="store_true", help="Output as JSON.")
    p_lane_doctor.set_defaults(func=cmd_lane_doctor)

    def _lane_help(args):
        p_lane.print_help()
        return 0

    p_lane.set_defaults(func=_lane_help)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    rc = args.func(args)
    sys.exit(rc)


if __name__ == "__main__":
    main()

# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 ProtocolWarden
"""
workstation_cli — command-line interface for WorkStation stack management.

Usage:
    python -m workstation_cli <command> [options]

Commands:
    up            Start the stack via docker compose.
    down          Stop the stack via docker compose.
    health        Check health endpoints and print results.
    health --json Output health results as JSON.
    status        Aggregate health + service info and print summary.
    status --json Output status summary as JSON.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from .config import load_config
from .health import check_all_health
from .lane_cli import cmd_lane_doctor, cmd_lane_health, cmd_lane_start, cmd_lane_status, cmd_lane_stop
from .status import aggregate_status

# ── Repo paths ────────────────────────────────────────────────────────────────

_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]          # tools/workstation_cli -> repo root
_COMPOSE_FILE = _REPO_ROOT / "compose" / "docker-compose.yml"
_CONFIG_DIR = _REPO_ROOT / "config" / "workstation"
_ENV_FILE = _REPO_ROOT / ".env"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compose(*args: str) -> int:
    """Run a docker compose command and return the exit code."""
    cmd = [
        "docker", "compose",
        "--file", str(_COMPOSE_FILE),
    ]
    if _ENV_FILE.exists():
        cmd += ["--env-file", str(_ENV_FILE)]
    cmd += list(args)
    # Long timeout — `console` wraps long-running interactive sessions.
    result = subprocess.run(cmd, timeout=86400)
    return result.returncode


def _load_or_die() -> dict:
    """Load service config from config/workstation/. Exit with message on failure."""
    endpoints_file = _CONFIG_DIR / "endpoints.yaml"
    if not endpoints_file.exists():
        sys.exit(1)
    try:
        cfg = load_config(_CONFIG_DIR)
    except Exception:
        sys.exit(1)
    return cfg.services


# ── Command handlers ──────────────────────────────────────────────────────────

def cmd_up(args: argparse.Namespace) -> int:
    """Start the stack in detached mode."""
    rc = _compose("up", "--detach", "--remove-orphans")
    if rc == 0:
        pass
    else:
        pass
    return rc


def cmd_down(args: argparse.Namespace) -> int:
    """Stop and remove stack containers."""
    rc = _compose("down", "--remove-orphans")
    if rc == 0:
        pass
    else:
        pass
    return rc


def cmd_health(args: argparse.Namespace) -> int:
    """Check health endpoints for all services."""
    services = _load_or_die()
    results = check_all_health(services)

    if args.json:
        all_ok = all(r["healthy"] for r in results.values())
        return 0 if all_ok else 1

    all_ok = True
    for name, result in results.items():
        "[OK]  " if result["healthy"] else "[FAIL]"
        result.get("status_code", "N/A")
        result.get("url", "")
        result.get("latency_ms")
        if result.get("error"):
            pass
        if not result["healthy"]:
            all_ok = False

    if all_ok:
        return 0
    else:
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Print aggregate status summary."""
    services = _load_or_die()
    summary = aggregate_status(services)

    if args.json:
        return 0 if summary.get("status") == "healthy" else 1


    platform_status = summary.get("status", "unknown")
    if platform_status == "healthy":
        pass
    elif platform_status == "degraded":
        pass
    else:
        pass

    for name, svc in summary.get("services", {}).items():
        svc.get("status") == "healthy"
        svc.get("base_url", "")
        getattr(services.get(name), "required", True)

    return 0 if platform_status == "healthy" else 1


# ── Argument parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workstation_cli",
        description="WorkStation stack management CLI.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # up
    p_up = sub.add_parser("up", help="Start the stack in detached mode.")
    p_up.set_defaults(func=cmd_up)

    # down
    p_down = sub.add_parser("down", help="Stop and remove stack containers.")
    p_down.set_defaults(func=cmd_down)

    # health
    p_health = sub.add_parser("health", help="Check health endpoints.")
    p_health.add_argument("--json", action="store_true", help="Output results as JSON.")
    p_health.set_defaults(func=cmd_health)

    # status
    p_status = sub.add_parser("status", help="Print aggregate status summary.")
    p_status.add_argument("--json", action="store_true", help="Output status as JSON.")
    p_status.set_defaults(func=cmd_status)

    # lane
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


# ── Entry point ───────────────────────────────────────────────────────────────

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

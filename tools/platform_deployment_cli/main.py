# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 ProtocolWarden
"""PlatformDeployment stack management CLI."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from .config import load_config
from .health import check_all_health
from .lane_cli import cmd_lane_doctor, cmd_lane_health, cmd_lane_start, cmd_lane_status, cmd_lane_stop
from .plane_cli import (
    cmd_plane_backup,
    cmd_plane_down,
    cmd_plane_list,
    cmd_plane_restore,
    cmd_plane_status,
    cmd_plane_up,
)
from .secrets_cli import cmd_secrets_backup, cmd_secrets_list, cmd_secrets_setup
from .status import aggregate_status
from .workers_cli import cmd_workers_restart, cmd_workers_start, cmd_workers_status, cmd_workers_stop

_LOG = logging.getLogger(__name__)

_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]
_COMPOSE_FILE = _REPO_ROOT / "compose" / "docker-compose.yml"
_CONFIG_DIR = _REPO_ROOT / "config" / "platformdeployment"
_ENV_FILE = _REPO_ROOT / ".env"


def _compose(*args: str) -> int:
    cmd = ["docker", "compose", "--file", str(_COMPOSE_FILE)]
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


# ---------------------------------------------------------------------------
# Stack commands
# ---------------------------------------------------------------------------

def cmd_up(args: argparse.Namespace) -> int:
    return _compose("up", "--detach", "--remove-orphans")


def cmd_down(args: argparse.Namespace) -> int:
    return _compose("down", "--remove-orphans")


def cmd_restart(args: argparse.Namespace) -> int:
    _LOG.info("=== PlatformDeployment: restarting stack ===")
    _LOG.info("Step 1/2  Stopping...")
    rc = _compose("down", "--remove-orphans")
    if rc != 0:
        return rc
    _LOG.info("Step 2/2  Starting...")
    return _compose("up", "--detach", "--remove-orphans")


def cmd_ensure_up(args: argparse.Namespace) -> int:
    import urllib.request
    port_switchboard = "20401"
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("PORT_SWITCHBOARD="):
                port_switchboard = line.split("=", 1)[1].strip()
    try:
        urllib.request.urlopen(f"http://localhost:{port_switchboard}/health", timeout=3)
        _LOG.info("stack already running and healthy (SwitchBoard: http://localhost:%s)", port_switchboard)
        return 0
    except Exception:
        pass
    _LOG.info("stack not running — starting...")
    return _compose("up", "--detach", "--remove-orphans", "--build")


def cmd_logs(args: argparse.Namespace) -> int:
    compose_args = ["logs", "--follow", f"--tail={args.tail}"]
    if args.service:
        compose_args.append(args.service)
    return _compose(*compose_args)


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


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="platform_deployment_cli",
        description="PlatformDeployment stack management CLI.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # -- Stack lifecycle -------------------------------------------------------
    p_up = sub.add_parser("up", help="Start the stack in detached mode.")
    p_up.set_defaults(func=cmd_up)

    p_down = sub.add_parser("down", help="Stop and remove stack containers.")
    p_down.set_defaults(func=cmd_down)

    p_restart = sub.add_parser("restart", help="Stop then start the stack.")
    p_restart.set_defaults(func=cmd_restart)

    p_ensure = sub.add_parser("ensure-up", help="Start the stack only if not already healthy.")
    p_ensure.set_defaults(func=cmd_ensure_up)

    p_logs = sub.add_parser("logs", help="Tail Docker Compose logs.")
    p_logs.add_argument("service", nargs="?", default="", help="Service name (omit for all).")
    p_logs.add_argument("--tail", default="50", metavar="N", help="Number of lines to show (default: 50).")
    p_logs.set_defaults(func=cmd_logs)

    p_health = sub.add_parser("health", help="Check health endpoints.")
    p_health.add_argument("--json", action="store_true", help="Output results as JSON.")
    p_health.set_defaults(func=cmd_health)

    p_status = sub.add_parser("status", help="Print aggregate status summary.")
    p_status.add_argument("--json", action="store_true", help="Output status as JSON.")
    p_status.set_defaults(func=cmd_status)

    # -- Lane subcommand group -------------------------------------------------
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
    p_lane_status.add_argument("--json", action="store_true")
    p_lane_status.set_defaults(func=cmd_lane_status)

    p_lane_health = lane_sub.add_parser("health", help="Run a live health check.")
    p_lane_health.add_argument("lane_name", nargs="?", default="aider_local")
    p_lane_health.add_argument("--json", action="store_true")
    p_lane_health.set_defaults(func=cmd_lane_health)

    p_lane_doctor = lane_sub.add_parser("doctor", help="Full pre-flight check for the lane.")
    p_lane_doctor.add_argument("lane_name", nargs="?", default="aider_local")
    p_lane_doctor.add_argument("--json", action="store_true")
    p_lane_doctor.set_defaults(func=cmd_lane_doctor)

    def _lane_help(args):
        p_lane.print_help()
        return 0

    p_lane.set_defaults(func=_lane_help)

    # -- Plane subcommand group ------------------------------------------------
    p_plane = sub.add_parser("plane", help="Manage Plane project tracker.")
    plane_sub = p_plane.add_subparsers(dest="plane_action", metavar="<action>")

    p_plane_up = plane_sub.add_parser("up", help="Install (if needed) and start Plane.")
    p_plane_up.set_defaults(func=cmd_plane_up)

    p_plane_down = plane_sub.add_parser("down", help="Stop Plane containers.")
    p_plane_down.set_defaults(func=cmd_plane_down)

    p_plane_status = plane_sub.add_parser("status", help="Check whether Plane is reachable.")
    p_plane_status.set_defaults(func=cmd_plane_status)

    p_plane_backup = plane_sub.add_parser("backup", help="pg_dump Plane database to ~/sync/platform/backups/.")
    p_plane_backup.set_defaults(func=cmd_plane_backup)

    p_plane_restore = plane_sub.add_parser("restore", help="Restore Plane database from a dump.")
    p_plane_restore.add_argument("dump", nargs="?", default="", help="Path to .sql.gz dump (omit for latest).")
    p_plane_restore.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt.")
    p_plane_restore.set_defaults(func=cmd_plane_restore)

    p_plane_list = plane_sub.add_parser("list", help="List available database dumps.")
    p_plane_list.set_defaults(func=cmd_plane_list)

    def _plane_help(args):
        p_plane.print_help()
        return 0

    p_plane.set_defaults(func=_plane_help)

    # -- Secrets subcommand group ----------------------------------------------
    p_secrets = sub.add_parser("secrets", help="Manage synced secrets (config files).")
    secrets_sub = p_secrets.add_subparsers(dest="secrets_action", metavar="<action>")

    p_secrets_backup = secrets_sub.add_parser("backup", help="Copy live config files to ~/sync/platform/config/.")
    p_secrets_backup.set_defaults(func=cmd_secrets_backup)

    p_secrets_setup = secrets_sub.add_parser("setup", help="Symlink config files from sync dir into repo.")
    p_secrets_setup.set_defaults(func=cmd_secrets_setup)

    p_secrets_list = secrets_sub.add_parser("list", help="Show backup and link status of each secret.")
    p_secrets_list.set_defaults(func=cmd_secrets_list)

    def _secrets_help(args):
        p_secrets.print_help()
        return 0

    p_secrets.set_defaults(func=_secrets_help)

    # -- Workers subcommand group ----------------------------------------------
    p_workers = sub.add_parser("workers", help="Manage OperationsCenter watcher lifecycle.")
    workers_sub = p_workers.add_subparsers(dest="workers_action", metavar="<action>")

    p_workers_start = workers_sub.add_parser("start", help="Start all watcher roles.")
    p_workers_start.set_defaults(func=cmd_workers_start)

    p_workers_stop = workers_sub.add_parser("stop", help="Stop all watcher roles.")
    p_workers_stop.set_defaults(func=cmd_workers_stop)

    p_workers_status = workers_sub.add_parser("status", help="Print watcher role status.")
    p_workers_status.set_defaults(func=cmd_workers_status)

    p_workers_restart = workers_sub.add_parser("restart", help="Stop then start all watcher roles.")
    p_workers_restart.set_defaults(func=cmd_workers_restart)

    def _workers_help(args):
        p_workers.print_help()
        return 0

    p_workers.set_defaults(func=_workers_help)

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

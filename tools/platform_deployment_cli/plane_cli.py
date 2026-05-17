# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 ProtocolWarden
"""Plane lifecycle and database backup/restore commands."""

from __future__ import annotations

import argparse
import gzip
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


_LOG = logging.getLogger(__name__)

_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]
_PLANE_DIR = _REPO_ROOT / "runtime" / "plane" / "plane-app"
_PLANE_ENV = _PLANE_DIR / "plane.env"
_PLANE_SH = _REPO_ROOT / "scripts" / "plane.sh"

_PLANE_APP_SERVICES = [
    "web", "api", "worker", "beat-worker", "space", "admin", "live",
]

# Default credentials match the docker-compose.yaml env defaults (not secrets).
_DEFAULT_PG_USER = "plane"
_DEFAULT_PG_DB = "plane"
_DEFAULT_PG_PASSWORD = "plane"  # noqa: S105 — docker-compose public default


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _load_plane_env() -> dict[str, str]:
    user = _DEFAULT_PG_USER
    password = _DEFAULT_PG_PASSWORD
    db = _DEFAULT_PG_DB

    if _PLANE_ENV.exists():
        for line in _PLANE_ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if key == "POSTGRES_USER":
                user = val
            elif key == "POSTGRES_PASSWORD":
                password = val
            elif key == "POSTGRES_DB":
                db = val

    return {
        "POSTGRES_USER": os.environ.get("POSTGRES_USER", user),
        "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", password),
        "POSTGRES_DB": os.environ.get("POSTGRES_DB", db),
    }


def _backup_dir() -> Path:
    return Path(os.environ.get("PLATFORM_BACKUPS_DIR", Path.home() / "sync" / "platform" / "backups"))


def _list_dumps() -> list[Path]:
    d = _backup_dir()
    if not d.exists():
        return []
    return sorted(d.glob("plane_*.sql.gz"), reverse=True)


# ---------------------------------------------------------------------------
# Lifecycle commands (delegate to plane.sh)
# ---------------------------------------------------------------------------

def _plane_sh(action: str) -> int:
    if not _PLANE_SH.exists():
        _LOG.error("plane.sh not found at %s", _PLANE_SH)
        return 1
    result = subprocess.run(["bash", str(_PLANE_SH), action], timeout=300)
    return result.returncode


def cmd_plane_up(args: argparse.Namespace) -> int:
    return _plane_sh("up")


def cmd_plane_down(args: argparse.Namespace) -> int:
    return _plane_sh("down")


def cmd_plane_status(args: argparse.Namespace) -> int:
    return _plane_sh("status")


# ---------------------------------------------------------------------------
# Backup commands
# ---------------------------------------------------------------------------

def cmd_plane_backup(args: argparse.Namespace) -> int:
    creds = _load_plane_env()
    dest = _backup_dir()
    dest.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outfile = dest / f"plane_{timestamp}.sql.gz"

    _LOG.info("dumping %s from plane-db → %s", creds["POSTGRES_DB"], outfile)

    dump_cmd = [
        "docker", "exec", "plane-db",
        "pg_dump", "-U", creds["POSTGRES_USER"], creds["POSTGRES_DB"],
    ]
    env = {**os.environ, "PGPASSWORD": creds["POSTGRES_PASSWORD"]}

    result = subprocess.run(dump_cmd, stdout=subprocess.PIPE, env=env, timeout=600)
    if result.returncode != 0:
        _LOG.error("pg_dump failed")
        outfile.unlink(missing_ok=True)
        return 1

    with gzip.open(outfile, "wb") as gz:
        gz.write(result.stdout)

    size = outfile.stat().st_size
    size_str = f"{size / 1024 / 1024:.1f}M" if size >= 1024 * 1024 else f"{size / 1024:.0f}K"
    _LOG.info("dump written: %s (%s)", outfile.name, size_str)

    keep = int(os.environ.get("PLANE_BACKUP_KEEP", "10"))
    for old in _list_dumps()[keep:]:
        old.unlink()
        _LOG.info("rotated: %s", old.name)

    _LOG.info("done — %s contains %d dump(s)", dest, len(_list_dumps()))
    return 0


def cmd_plane_restore(args: argparse.Namespace) -> int:
    creds = _load_plane_env()

    dump_path = getattr(args, "dump", "") or ""
    if dump_path:
        dump_file = Path(dump_path)
    else:
        dumps = _list_dumps()
        if not dumps:
            _LOG.error("no dumps found in %s", _backup_dir())
            return 1
        dump_file = dumps[0]

    if not dump_file.exists():
        _LOG.error("dump file not found: %s", dump_file)
        return 1

    _LOG.info("restoring from: %s", dump_file)
    _LOG.info("target: %s on plane-db", creds["POSTGRES_DB"])

    if not getattr(args, "yes", False):
        answer = input(f"\nthis will DROP and recreate '{creds['POSTGRES_DB']}'. continue? [y/N] ")
        if answer.strip().lower() != "y":
            _LOG.info("aborted")
            return 0

    env = {**os.environ, "PGPASSWORD": creds["POSTGRES_PASSWORD"]}

    _LOG.info("stopping Plane app services...")
    subprocess.run(
        ["docker", "compose", "-f", str(_PLANE_DIR / "docker-compose.yaml"),
         "--env-file", str(_PLANE_ENV), "stop", *_PLANE_APP_SERVICES],
        env=env, timeout=120,
    )

    _LOG.info("dropping and recreating database...")
    drop_sql = (
        f'DROP DATABASE IF EXISTS "{creds["POSTGRES_DB"]}"; '
        f'CREATE DATABASE "{creds["POSTGRES_DB"]}" OWNER "{creds["POSTGRES_USER"]}";'
    )
    result = subprocess.run(
        ["docker", "exec", "plane-db",
         "psql", "-U", creds["POSTGRES_USER"], "-d", "postgres", "-c", drop_sql],
        env=env, timeout=60,
    )
    if result.returncode != 0:
        _LOG.error("failed to recreate database")
        return 1

    _LOG.info("loading dump...")
    with gzip.open(dump_file, "rb") as gz:
        data = gz.read()

    result = subprocess.run(
        ["docker", "exec", "-i", "plane-db",
         "psql", "-U", creds["POSTGRES_USER"], "-d", creds["POSTGRES_DB"], "-q"],
        input=data, env=env, timeout=600,
    )
    if result.returncode != 0:
        _LOG.error("psql load failed")
        return 1

    _LOG.info("restarting Plane app services...")
    subprocess.run(
        ["docker", "compose", "-f", str(_PLANE_DIR / "docker-compose.yaml"),
         "--env-file", str(_PLANE_ENV), "start", *_PLANE_APP_SERVICES],
        env=env, timeout=120,
    )

    _LOG.info("done — restore complete from %s", dump_file.name)
    return 0


def cmd_plane_list(args: argparse.Namespace) -> int:
    dumps = _list_dumps()
    if not dumps:
        _LOG.info("no dumps in %s", _backup_dir())
        return 0
    for d in dumps:
        size = d.stat().st_size
        size_str = f"{size / 1024 / 1024:.1f}M" if size >= 1024 * 1024 else f"{size / 1024:.0f}K"
        _LOG.info("%s  %s", d.name, size_str)
    return 0

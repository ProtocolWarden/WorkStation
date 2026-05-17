# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 ProtocolWarden
"""Secrets backup and setup commands."""

from __future__ import annotations

import argparse
import logging
import os
import shutil
from pathlib import Path


_LOG = logging.getLogger(__name__)

_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]

_SECRET_FILES = [
    ".env",
    "config/switchboard/policy.yaml",
    "config/workstation/endpoints.yaml",
    "runtime/plane/plane-app/plane.env",
]


def _secrets_dir() -> Path:
    return Path(os.environ.get("PLATFORM_SECRETS_DIR", Path.home() / "sync" / "platform" / "config"))


def _flat_name(rel: str) -> str:
    return rel.replace("/", "__")


def cmd_secrets_backup(args: argparse.Namespace) -> int:
    dest = _secrets_dir()
    dest.mkdir(parents=True, exist_ok=True)
    any_backed_up = False
    for rel in _SECRET_FILES:
        src = _REPO_ROOT / rel
        dst = dest / _flat_name(rel)
        if src.exists():
            shutil.copy2(src, dst)
            _LOG.info("backed up: %s → %s", rel, dst)
            any_backed_up = True
        else:
            _LOG.info("skipped (not found): %s", rel)
    if any_backed_up:
        _LOG.info("done — secrets backed up to %s", dest)
    return 0


def cmd_secrets_setup(args: argparse.Namespace) -> int:
    src_dir = _secrets_dir()
    for rel in _SECRET_FILES:
        flat = _flat_name(rel)
        src = src_dir / flat
        dst = _REPO_ROOT / rel

        if not src.exists():
            _LOG.info("skipped (not in sync dir): %s", rel)
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        _LOG.info("restored: %s", rel)

    _LOG.info("done — secrets copied into repo")
    return 0


def cmd_secrets_list(args: argparse.Namespace) -> int:
    src_dir = _secrets_dir()
    _LOG.info("secrets dir: %s", src_dir)
    for rel in _SECRET_FILES:
        flat = _flat_name(rel)
        src = src_dir / flat
        dst = _REPO_ROOT / rel
        backed_up = "✓" if src.exists() else "✗"
        linked = "linked" if dst.is_symlink() else ("file" if dst.exists() else "missing")
        _LOG.info("  %s %-50s repo: %s", backed_up, rel, linked)
    return 0

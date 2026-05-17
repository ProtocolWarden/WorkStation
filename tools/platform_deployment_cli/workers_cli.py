# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 ProtocolWarden
"""Workers (OperationsCenter watcher lifecycle) commands."""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
from pathlib import Path


_LOG = logging.getLogger(__name__)

_OC_DEFAULT = Path.home() / "Documents" / "GitHub" / "OperationsCenter"


def _oc_script() -> Path | None:
    oc_root = Path(os.environ.get("OPERATIONS_CENTER_ROOT", str(_OC_DEFAULT)))
    script = oc_root / "scripts" / "operations-center.sh"
    return script if script.exists() else None


def _run_oc(action: str) -> int:
    script = _oc_script()
    if script is None:
        oc_root = os.environ.get("OPERATIONS_CENTER_ROOT", str(_OC_DEFAULT))
        _LOG.warning("OperationsCenter not found at %s — set OPERATIONS_CENTER_ROOT to override", oc_root)
        return 0
    result = subprocess.run(["bash", str(script), action], timeout=120)
    return result.returncode


def cmd_workers_start(args: argparse.Namespace) -> int:
    _LOG.info("starting OperationsCenter watchers...")
    return _run_oc("watch-all")


def cmd_workers_stop(args: argparse.Namespace) -> int:
    _LOG.info("stopping OperationsCenter watchers...")
    return _run_oc("watch-all-stop")


def cmd_workers_status(args: argparse.Namespace) -> int:
    return _run_oc("watch-all-status")


def cmd_workers_restart(args: argparse.Namespace) -> int:
    _LOG.info("restarting OperationsCenter watchers...")
    rc = _run_oc("watch-all-stop")
    if rc != 0:
        return rc
    return _run_oc("watch-all")

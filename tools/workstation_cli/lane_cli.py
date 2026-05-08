# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 Velascat
"""
lane_cli.py — CLI commands for the aider_local execution lane.

Subcommand group: workstation_cli lane <action> [lane_name]

  lane start    [lane_name]   Start local model services for the lane.
  lane stop     [lane_name]   Stop local model services for the lane.
  lane status   [lane_name]   Show current lane state and model health.
  lane health   [lane_name]   Perform a live health check and show results.

If lane_name is omitted, defaults to 'aider_local' (the only lane in Phase 2).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from .lane_config import LocalLaneConfig, default_local_lane_config, load_local_lane_config
from .lane_manager import LocalLaneManager
from .lane_models import LaneState, LaneStatus

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_LANE_CONFIG = _REPO_ROOT / "config" / "workstation" / "local_lane.yaml"
_AIDER_LOCAL = "aider_local"


# ---------------------------------------------------------------------------
# Config loading helper
# ---------------------------------------------------------------------------

def _load_lane_config(config_path: Optional[Path] = None) -> LocalLaneConfig:
    path = config_path or _DEFAULT_LANE_CONFIG
    if not path.exists():
        # Return a disabled default rather than crashing — lets status show
        # a clear "not configured" message.
        return default_local_lane_config()
    try:
        return load_local_lane_config(path)
    except Exception:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _print_status(status: LaneStatus, *, json_output: bool = False) -> None:
    if json_output:
        return

    state_color = {
        LaneState.READY: "\033[32m",
        LaneState.UNHEALTHY: "\033[31m",
        LaneState.FAILED: "\033[31m",
        LaneState.STARTING: "\033[33m",
        LaneState.DISABLED: "\033[90m",
        LaneState.STOPPED: "\033[90m",
        LaneState.CONFIGURED: "\033[33m",
    }
    state_color.get(status.state, "")


    if status.failure_reason:
        pass

    if status.models:
        for m in status.models:
            if m.failure_reason:
                pass
    elif status.state not in (LaneState.DISABLED, LaneState.STOPPED):
        pass



# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_lane_start(args) -> int:
    lane_name = getattr(args, "lane_name", _AIDER_LOCAL) or _AIDER_LOCAL
    config = _load_lane_config(getattr(args, "config", None))

    if config.lane_name != lane_name and lane_name != _AIDER_LOCAL:
        return 1

    if not config.enabled:
        return 1


    if not config.models:
        return 1

    managed = [m.name for m in config.models if m.managed]
    unmanaged = [m.name for m in config.models if not m.managed]

    if managed:
        pass
    if unmanaged:
        pass

    manager = LocalLaneManager(config)
    status = manager.start()
    _print_status(status)

    if status.ready:
        return 0
    else:
        return 1


def cmd_lane_stop(args) -> int:
    lane_name = getattr(args, "lane_name", _AIDER_LOCAL) or _AIDER_LOCAL
    config = _load_lane_config(getattr(args, "config", None))

    if config.lane_name != lane_name and lane_name != _AIDER_LOCAL:
        return 1


    manager = LocalLaneManager(config)
    manager.stop()
    return 0


def cmd_lane_status(args) -> int:
    getattr(args, "lane_name", _AIDER_LOCAL) or _AIDER_LOCAL
    json_output = getattr(args, "json", False)
    config = _load_lane_config(getattr(args, "config", None))

    if not json_output:
        pass

    manager = LocalLaneManager(config)
    status = manager.get_status()
    _print_status(status, json_output=json_output)

    return 0 if status.ready else 1


def cmd_lane_health(args) -> int:
    getattr(args, "lane_name", _AIDER_LOCAL) or _AIDER_LOCAL
    json_output = getattr(args, "json", False)
    config = _load_lane_config(getattr(args, "config", None))

    if not json_output:
        pass

    manager = LocalLaneManager(config)
    status = manager.check_health()
    _print_status(status, json_output=json_output)

    return 0 if status.ready else 1


def cmd_lane_doctor(args) -> int:
    """Full pre-flight check for the aider_local lane."""
    import shutil

    json_output = getattr(args, "json", False)
    config_path = getattr(args, "config", None)

    checks: list[tuple[str, bool, str]] = []  # (label, passed, detail)

    # 1. Config file exists
    path = config_path or _REPO_ROOT / "config" / "workstation" / "local_lane.yaml"
    config_exists = path is not None and Path(path).exists()
    checks.append(("config file", config_exists, str(path) if config_exists else f"not found at {path}"))

    # 2. Config parses
    config = None
    if config_exists:
        try:
            from .lane_config import load_local_lane_config
            config = load_local_lane_config(Path(path))
            checks.append(("config parses", True, f"lane={config.lane_name}, enabled={config.enabled}"))
        except Exception as exc:
            checks.append(("config parses", False, str(exc)))
    else:
        config = None
        checks.append(("config parses", False, "skipped — no config file"))

    # 3. Lane is enabled
    enabled = config is not None and config.enabled
    checks.append(("lane enabled", enabled, "" if enabled else "set lane.enabled: true in config"))

    # 4. aider binary
    aider_path = shutil.which("aider")
    checks.append(("aider binary", aider_path is not None, aider_path or "not found in PATH"))

    # 5. Ollama reachable (check first model endpoint)
    ollama_ok = False
    ollama_detail = "no models configured"
    if config and config.models:
        model = config.models[0]
        try:
            import urllib.request
            urllib.request.urlopen(model.health_url, timeout=5)
            ollama_ok = True
            ollama_detail = f"reachable at {model.endpoint}"
        except Exception as exc:
            ollama_detail = f"{model.endpoint} — {type(exc).__name__}: {exc}"
    checks.append(("ollama reachable", ollama_ok, ollama_detail))

    # 6. Models configured
    model_count = len(config.models) if config else 0
    checks.append(("models configured", model_count > 0, f"{model_count} model(s)"))

    all_passed = all(passed for _, passed, _ in checks)

    if json_output:
        pass
    else:
        for label, passed, detail in checks:
            pass
        if all_passed:
            pass
        else:
            pass

    return 0 if all_passed else 1

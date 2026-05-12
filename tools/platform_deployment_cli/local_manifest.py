# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 ProtocolWarden
"""LocalManifest path discovery for PlatformDeployment."""

from __future__ import annotations

import os
import re
from pathlib import Path

_PROJECT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

ENV_OVERRIDE = "PLATFORM_DEPLOYMENT_LOCAL_MANIFEST"
USER_CONFIG_SUBDIR = "platformdeployment/manifests"
REPO_LOCAL_PATH = Path("topology") / "local_manifest.yaml"


class LocalManifestDiscoveryError(ValueError):
    """Raised on invalid project names or other discovery preconditions."""


def discover_local_manifest(
    project: str,
    *,
    repo_root: Path | None = None,
) -> Path | None:
    if not _PROJECT_NAME_PATTERN.match(project):
        raise LocalManifestDiscoveryError(
            f"invalid project slug {project!r}; must match {_PROJECT_NAME_PATTERN.pattern}"
        )

    for candidate in candidate_paths(project, repo_root=repo_root):
        if candidate.is_file():
            return candidate
    return None


def candidate_paths(
    project: str,
    *,
    repo_root: Path | None = None,
) -> list[Path]:
    out: list[Path] = []

    override = os.environ.get(ENV_OVERRIDE)
    if override:
        out.append(Path(override).expanduser())

    out.append(_user_config_path(project))

    if repo_root is not None:
        out.append(Path(repo_root) / REPO_LOCAL_PATH)

    return out


def user_config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / USER_CONFIG_SUBDIR


def _user_config_path(project: str) -> Path:
    return user_config_dir() / f"{project}.local.yaml"


__all__ = [
    "ENV_OVERRIDE",
    "LocalManifestDiscoveryError",
    "REPO_LOCAL_PATH",
    "USER_CONFIG_SUBDIR",
    "candidate_paths",
    "discover_local_manifest",
    "user_config_dir",
]

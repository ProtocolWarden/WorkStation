# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 ProtocolWarden
"""LocalManifest path discovery.

WorkStation owns local-runtime infrastructure, including knowing where
each project keeps its operator-local config. Per the PlatformManifest
design, WorkStation provides discovery of a project's LocalManifest
path; OperationsCenter consumes the resolved path to compose its
EffectiveRepoGraph.

Discovery order (first match wins):

1. ``$WORKSTATION_LOCAL_MANIFEST`` — explicit override for ad-hoc/test use.
2. ``$XDG_CONFIG_HOME/workstation/manifests/<project>.local.yaml``
   (falls back to ``~/.config/workstation/manifests/<project>.local.yaml``).
3. If ``repo_root`` is given: ``<repo_root>/topology/local_manifest.yaml``
   (the single-repo-project convention from the design doc).

Returns ``None`` when no manifest is found. Callers may treat this as
"deployment has no local overrides" — the EffectiveRepoGraph is then
just PlatformManifest + ProjectManifest.

This module deliberately does **not** read or validate the manifest.
That is PlatformManifest's job. WorkStation only resolves the path.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

_PROJECT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

# Env var name an operator can set to override discovery entirely.
ENV_OVERRIDE = "WORKSTATION_LOCAL_MANIFEST"

# Subdir under XDG_CONFIG_HOME (default ~/.config).
USER_CONFIG_SUBDIR = "workstation/manifests"

# Single-repo-project convention.
REPO_LOCAL_PATH = Path("topology") / "local_manifest.yaml"


class LocalManifestDiscoveryError(ValueError):
    """Raised on invalid project names or other discovery preconditions."""


def discover_local_manifest(
    project: str,
    *,
    repo_root: Path | None = None,
) -> Path | None:
    """Resolve a LocalManifest path for the given project.

    ``project`` is the project's slug (lowercase, alphanumeric + ``_-``).
    Returns the first existing path matched by the order in this
    module's docstring, or ``None`` if no candidate exists on disk.
    """
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
    """Return the ordered list of paths that ``discover_local_manifest``
    will check, regardless of which exist. Useful for diagnostics.
    """
    out: list[Path] = []

    override = os.environ.get(ENV_OVERRIDE)
    if override:
        out.append(Path(override).expanduser())

    out.append(_user_config_path(project))

    if repo_root is not None:
        out.append(Path(repo_root) / REPO_LOCAL_PATH)

    return out


def user_config_dir() -> Path:
    """The directory under which per-project local manifests are kept."""
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

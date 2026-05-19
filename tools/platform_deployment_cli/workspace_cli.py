# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 ProtocolWarden
"""Workspace commands — clone and sync all PlatformManifest repos."""

from __future__ import annotations

import argparse
import logging
import subprocess
from pathlib import Path

try:
    import yaml  # type: ignore[import-untyped]
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

_LOG = logging.getLogger(__name__)

_MANIFEST_DEFAULT = (
    Path.home() / "Documents" / "GitHub" / "PlatformManifest"
    / "src" / "platform_manifest" / "data" / "platform_manifest.yaml"
)
_GITHUB_DIR = Path.home() / "Documents" / "GitHub"


def _load_manifest(manifest_path: Path) -> list[dict]:
    """Return list of {canonical_name, github_url} dicts from the manifest."""
    if not manifest_path.exists():
        _LOG.error("platform_manifest.yaml not found at %s", manifest_path)
        _LOG.error("Set PLATFORM_MANIFEST_PATH env var to override.")
        return []

    if not _YAML_AVAILABLE:
        _LOG.error("PyYAML is not installed — cannot parse platform_manifest.yaml")
        _LOG.error("Install it with: pip install pyyaml")
        return []

    with manifest_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    repos_section = data.get("repos", {})
    entries = []
    for _key, repo in repos_section.items():
        canonical_name = repo.get("canonical_name")
        github_url = repo.get("github_url")
        if canonical_name and github_url:
            entries.append({"canonical_name": canonical_name, "github_url": github_url})
    return entries


def cmd_workspace_clone_all(args: argparse.Namespace) -> int:
    """Clone all repos listed in PlatformManifest into ~/Documents/GitHub/."""
    import os

    manifest_path = Path(
        os.environ.get("PLATFORM_MANIFEST_PATH", str(_MANIFEST_DEFAULT))
    )
    pull = getattr(args, "pull", False)

    repos = _load_manifest(manifest_path)
    if not repos:
        return 1

    cloned: list[str] = []
    pulled: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

    for repo in repos:
        name = repo["canonical_name"]
        url = repo["github_url"]
        dest = _GITHUB_DIR / name

        if dest.exists():
            if pull:
                _LOG.info("[pull]  %s -> %s", name, dest)
                result = subprocess.run(
                    ["git", "-C", str(dest), "pull", "--ff-only"],
                    timeout=120,
                )
                if result.returncode == 0:
                    pulled.append(name)
                else:
                    _LOG.warning("pull failed for %s (rc=%d)", name, result.returncode)
                    failed.append(name)
            else:
                _LOG.info("[skip]  %s (already exists at %s)", name, dest)
                skipped.append(name)
        else:
            _LOG.info("[clone] %s -> %s", name, dest)
            result = subprocess.run(
                ["git", "clone", url, str(dest)],
                timeout=300,
            )
            if result.returncode == 0:
                cloned.append(name)
            else:
                _LOG.warning("clone failed for %s (rc=%d)", name, result.returncode)
                failed.append(name)

    # Summary
    _LOG.info("")
    _LOG.info("=== workspace clone-all summary ===")
    _LOG.info("  cloned:  %d  %s", len(cloned), cloned)
    if pull:
        _LOG.info("  pulled:  %d  %s", len(pulled), pulled)
    _LOG.info("  skipped: %d  %s", len(skipped), skipped)
    if failed:
        _LOG.warning("  FAILED:  %d  %s", len(failed), failed)

    return 1 if failed else 0

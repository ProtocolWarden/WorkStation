# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 Velascat
"""Discovery tests for tools.workstation_cli.local_manifest."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from workstation_cli.local_manifest import (
    ENV_OVERRIDE,
    LocalManifestDiscoveryError,
    REPO_LOCAL_PATH,
    candidate_paths,
    discover_local_manifest,
    user_config_dir,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each test starts with no override and a tmp XDG_CONFIG_HOME."""
    monkeypatch.delenv(ENV_OVERRIDE, raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)


# ---------------------------------------------------------------------------
# user_config_dir
# ---------------------------------------------------------------------------


class TestUserConfigDir:
    def test_default_is_under_home(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        d = user_config_dir()
        assert d == tmp_path / ".config" / "workstation" / "manifests"

    def test_xdg_config_home_respected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        d = user_config_dir()
        assert d == tmp_path / "xdg" / "workstation" / "manifests"


# ---------------------------------------------------------------------------
# candidate_paths
# ---------------------------------------------------------------------------


class TestCandidatePaths:
    def test_only_user_config_when_no_override_no_repo_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        candidates = candidate_paths("vfa")
        assert candidates == [
            tmp_path / "xdg" / "workstation" / "manifests" / "vfa.local.yaml"
        ]

    def test_override_first_then_user_then_repo(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv(ENV_OVERRIDE, "/some/explicit/path.yaml")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        candidates = candidate_paths("vfa", repo_root=tmp_path / "repo")
        assert candidates[0] == Path("/some/explicit/path.yaml")
        assert candidates[1] == (
            tmp_path / "xdg" / "workstation" / "manifests" / "vfa.local.yaml"
        )
        assert candidates[2] == tmp_path / "repo" / REPO_LOCAL_PATH

    def test_override_expands_user(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # Path.expanduser reads $HOME, not Path.home(); set both for safety.
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv(ENV_OVERRIDE, "~/explicit.yaml")
        candidates = candidate_paths("vfa")
        assert candidates[0] == tmp_path / "explicit.yaml"


# ---------------------------------------------------------------------------
# discover_local_manifest
# ---------------------------------------------------------------------------


class TestDiscover:
    def test_returns_none_when_nothing_present(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        assert discover_local_manifest("vfa") is None

    def test_finds_user_config_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        xdg = tmp_path / "xdg"
        manifests = xdg / "workstation" / "manifests"
        manifests.mkdir(parents=True)
        target = manifests / "vfa.local.yaml"
        target.write_text("manifest_kind: local\nmanifest_version: '1.0.0'\n", encoding="utf-8")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
        assert discover_local_manifest("vfa") == target

    def test_finds_repo_root_topology_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        repo = tmp_path / "repo"
        topology = repo / "topology"
        topology.mkdir(parents=True)
        target = topology / "local_manifest.yaml"
        target.write_text("manifest_kind: local\nmanifest_version: '1.0.0'\n", encoding="utf-8")
        assert discover_local_manifest("vfa", repo_root=repo) == target

    def test_override_wins_over_user_config(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # User config exists
        xdg = tmp_path / "xdg"
        manifests = xdg / "workstation" / "manifests"
        manifests.mkdir(parents=True)
        user_target = manifests / "vfa.local.yaml"
        user_target.write_text("# user config\n", encoding="utf-8")
        # Override path also exists, and should win
        explicit = tmp_path / "explicit.yaml"
        explicit.write_text("# explicit\n", encoding="utf-8")
        monkeypatch.setenv(ENV_OVERRIDE, str(explicit))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
        assert discover_local_manifest("vfa") == explicit

    def test_user_config_wins_over_repo_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        xdg = tmp_path / "xdg"
        manifests = xdg / "workstation" / "manifests"
        manifests.mkdir(parents=True)
        user_target = manifests / "vfa.local.yaml"
        user_target.write_text("# user\n", encoding="utf-8")
        repo = tmp_path / "repo"
        topology = repo / "topology"
        topology.mkdir(parents=True)
        (topology / "local_manifest.yaml").write_text("# repo\n", encoding="utf-8")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
        assert discover_local_manifest("vfa", repo_root=repo) == user_target


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestProjectNameValidation:
    @pytest.mark.parametrize(
        "name",
        [
            "Video-Foundry",  # uppercase
            "with spaces",
            "../escape",
            "",
            "trailing-",  # actually OK by regex; just to be sure
        ],
    )
    def test_invalid_names_raise(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str
    ) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        if name == "trailing-":
            # actually a valid slug; assert it does NOT raise
            assert discover_local_manifest(name) is None
            return
        with pytest.raises(LocalManifestDiscoveryError):
            discover_local_manifest(name)

    def test_valid_names_accepted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        for name in ("vfa", "video-foundry", "video_foundry", "vf2", "0pinion"):
            # Should resolve to None (no file), not raise
            assert discover_local_manifest(name) is None

# SPDX-License-Identifier: SSPL-1.0
# Copyright (C) 2026 ProtocolWarden
"""PlatformDeployment CLI package."""

from .local_manifest import (
    ENV_OVERRIDE,
    LocalManifestDiscoveryError,
    REPO_LOCAL_PATH,
    USER_CONFIG_SUBDIR,
    candidate_paths,
    discover_local_manifest,
    user_config_dir,
)

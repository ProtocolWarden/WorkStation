#!/usr/bin/env bash
# backup-secrets.sh — copy live gitignored config files to ~/sync/platform/config/
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${PLATFORM_SECRETS_DIR:-$HOME/sync/platform/config}"

mkdir -p "$DEST"

files=(
    ".env"
    "config/switchboard/policy.yaml"
    "config/workstation/endpoints.yaml"
    "runtime/plane/plane-app/plane.env"
)

for f in "${files[@]}"; do
    src="$REPO_ROOT/$f"
    dst="$DEST/$(echo "$f" | tr '/' '__')"
    if [ -f "$src" ]; then
        cp "$src" "$dst"
        echo "backed up: $f → $dst"
    else
        echo "skipped (not found): $f"
    fi
done

echo "done — secrets backed up to $DEST"

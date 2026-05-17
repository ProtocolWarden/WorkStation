#!/usr/bin/env bash
# setup-secrets.sh — symlink secrets from ~/sync/platform/config/ into the repo
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${PLATFORM_SECRETS_DIR:-$HOME/sync/platform/config}"

if [ ! -d "$SRC" ]; then
    echo "error: secrets dir not found: $SRC"
    echo "  set PLATFORM_SECRETS_DIR or ensure ~/sync/platform/config/ exists"
    exit 1
fi

declare -A files=(
    [".env"]=".env"
    ["config/switchboard/policy.yaml"]="config/switchboard/policy.yaml"
    ["config/workstation/endpoints.yaml"]="config/workstation/endpoints.yaml"
    ["runtime/plane/plane-app/plane.env"]="runtime/plane/plane-app/plane.env"
)

for repo_path in "${!files[@]}"; do
    flat_name="$(echo "$repo_path" | tr '/' '__')"
    secret_file="$SRC/$flat_name"
    target="$REPO_ROOT/$repo_path"

    if [ ! -f "$secret_file" ]; then
        echo "skipped (not in secrets dir): $repo_path"
        continue
    fi

    mkdir -p "$(dirname "$target")"

    if [ -L "$target" ]; then
        rm "$target"
    elif [ -f "$target" ]; then
        echo "warning: $repo_path already exists as a regular file — skipping (remove manually to replace with symlink)"
        continue
    fi

    ln -s "$secret_file" "$target"
    echo "linked: $repo_path → $secret_file"
done

echo "done — secrets linked into repo"

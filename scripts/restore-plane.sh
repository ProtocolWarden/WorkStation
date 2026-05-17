#!/usr/bin/env bash
# restore-plane.sh — restore a Plane pg_dump into the plane-db container
# Usage: restore-plane.sh [path/to/dump.sql.gz]
#   If no path given, uses the most recent dump in ~/sync/platform/backups/
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${PLATFORM_BACKUPS_DIR:-$HOME/sync/platform/backups}"
COMPOSE_DIR="$REPO_ROOT/runtime/plane/plane-app"
ENV_FILE="$COMPOSE_DIR/plane.env"

POSTGRES_USER="${POSTGRES_USER:-plane}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-plane}"
POSTGRES_DB="${POSTGRES_DB:-plane}"

if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
        key="${key%%[[:space:]]*}"
        value="${value%%[[:space:]]*}"
        case "$key" in
            POSTGRES_USER)     POSTGRES_USER="$value" ;;
            POSTGRES_PASSWORD) POSTGRES_PASSWORD="$value" ;;
            POSTGRES_DB)       POSTGRES_DB="$value" ;;
        esac
    done < "$ENV_FILE"
fi

# Resolve dump file
if [ $# -ge 1 ]; then
    DUMP_FILE="$1"
else
    DUMP_FILE="$(ls -1t "$BACKUP_DIR"/plane_*.sql.gz 2>/dev/null | head -1)"
    if [ -z "$DUMP_FILE" ]; then
        echo "error: no dumps found in $BACKUP_DIR" >&2
        exit 1
    fi
fi

if [ ! -f "$DUMP_FILE" ]; then
    echo "error: dump file not found: $DUMP_FILE" >&2
    exit 1
fi

echo "restoring from: $DUMP_FILE"
echo "target: $POSTGRES_DB on plane-db"
echo ""
read -r -p "this will DROP and recreate '$POSTGRES_DB'. continue? [y/N] " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { echo "aborted"; exit 0; }

echo "stopping Plane app services..."
docker compose -f "$COMPOSE_DIR/docker-compose.yaml" --env-file "$ENV_FILE" \
    stop web api worker beat-worker space admin live 2>/dev/null || true

echo "dropping and recreating database..."
docker exec plane-db \
    env PGPASSWORD="$POSTGRES_PASSWORD" \
    psql -U "$POSTGRES_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS \"$POSTGRES_DB\";" \
    -c "CREATE DATABASE \"$POSTGRES_DB\" OWNER \"$POSTGRES_USER\";"

echo "loading dump..."
gunzip -c "$DUMP_FILE" | docker exec -i plane-db \
    env PGPASSWORD="$POSTGRES_PASSWORD" \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q

echo "restarting Plane app services..."
docker compose -f "$COMPOSE_DIR/docker-compose.yaml" --env-file "$ENV_FILE" \
    start web api worker beat-worker space admin live 2>/dev/null || true

echo "done — restore complete from $(basename "$DUMP_FILE")"

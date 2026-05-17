#!/usr/bin/env bash
# backup-plane.sh — pg_dump the Plane database into ~/sync/platform/backups/
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${PLATFORM_BACKUPS_DIR:-$HOME/sync/platform/backups}"
KEEP="${PLANE_BACKUP_KEEP:-10}"

COMPOSE_DIR="$REPO_ROOT/runtime/plane/plane-app"
ENV_FILE="$COMPOSE_DIR/plane.env"

# Load DB credentials from plane.env if present
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

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTFILE="$BACKUP_DIR/plane_${TIMESTAMP}.sql.gz"

echo "dumping $POSTGRES_DB from plane-db → $OUTFILE"

docker exec plane-db \
    env PGPASSWORD="$POSTGRES_PASSWORD" \
    pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
    | gzip > "$OUTFILE"

echo "dump written: $OUTFILE ($(du -sh "$OUTFILE" | cut -f1))"

# Rotate: keep the N most recent dumps
mapfile -t dumps < <(ls -1t "$BACKUP_DIR"/plane_*.sql.gz 2>/dev/null)
if (( ${#dumps[@]} > KEEP )); then
    for old in "${dumps[@]:$KEEP}"; do
        rm -f "$old"
        echo "rotated: $old"
    done
fi

echo "done — $BACKUP_DIR contains $(ls "$BACKUP_DIR"/plane_*.sql.gz 2>/dev/null | wc -l) dump(s)"

#!/bin/bash
# 每日自动备份：pg_dump 自定义格式 + gzip，保留 14 天。
# 由 docker-compose 的 backup 服务作为 entrypoint 长驻运行。
set -uo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
INTERVAL="${BACKUP_INTERVAL_SECONDS:-86400}"

mkdir -p "$BACKUP_DIR"

run_backup() {
  local ts file
  ts="$(date +%Y%m%d_%H%M%S)"
  file="$BACKUP_DIR/pwb_${ts}.dump"

  if pg_dump -Fc -f "$file"; then
    gzip -f "$file"
    echo "[backup] $(date '+%F %T') created ${file}.gz ($(du -h "${file}.gz" | cut -f1))"
  else
    echo "[backup] $(date '+%F %T') FAILED" >&2
    rm -f "$file"
    return 1
  fi

  find "$BACKUP_DIR" -name 'pwb_*.dump.gz' -mtime "+${RETENTION_DAYS}" -print -delete \
    | sed 's/^/[backup] pruned /'
}

echo "[backup] start, dir=$BACKUP_DIR retention=${RETENTION_DAYS}d interval=${INTERVAL}s"

# 启动即备份一次，之后按间隔循环
run_backup
while true; do
  sleep "$INTERVAL"
  run_backup
done

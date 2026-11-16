#!/bin/bash
# 从备份文件恢复。
# 用法（在项目根目录）：
#   bash scripts/restore.sh backups/pwb_20261115_030000.dump.gz
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "用法: restore.sh <备份文件路径>" >&2
  exit 1
fi

SRC="$1"
if [ ! -f "$SRC" ]; then
  echo "备份文件不存在: $SRC" >&2
  exit 1
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

case "$SRC" in
  *.gz)
    gzip -dc "$SRC" > "$WORK/restore.dump"
    ;;
  *)
    cp "$SRC" "$WORK/restore.dump"
    ;;
esac

echo "==> 停止 api，避免写入冲突"
docker compose stop api

echo "==> 重建数据库结构"
docker compose exec -T db psql -U "${POSTGRES_USER:-pwb}" -d postgres \
  -c "DROP DATABASE IF EXISTS ${POSTGRES_DB:-personal_workbench};" \
  -c "CREATE DATABASE ${POSTGRES_DB:-personal_workbench};"

echo "==> 导入备份"
docker compose exec -T db pg_restore \
  -U "${POSTGRES_USER:-pwb}" \
  -d "${POSTGRES_DB:-personal_workbench}" \
  --no-owner --clean --if-exists < "$WORK/restore.dump"

echo "==> 重启 api"
docker compose start api

echo "恢复完成"

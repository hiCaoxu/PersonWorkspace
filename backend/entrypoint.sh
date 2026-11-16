#!/bin/sh
set -e

echo "[entrypoint] 执行数据库迁移"
alembic upgrade head

echo "[entrypoint] 写入幂等种子"
python -m app.db.seed

echo "[entrypoint] 启动 API"
# 默认单 worker：定时任务无需重复调度，个人自用并发极低
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-1}" \
    --proxy-headers \
    --forwarded-allow-ips="*"

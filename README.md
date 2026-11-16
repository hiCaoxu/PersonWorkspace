# 个人工作台

一个只给自己用的长期工作台：待办、日记、笔记、健康、娱乐、记账与档案，八个模块共用同一份服务端数据。
电脑、手机、平板打开同一个地址即可看到同样的内容，也可以安装到桌面（PWA）离线打开外壳。

界面为米白暖调极简风：米白底、白卡片浅褐描边、单一暖褐强调色、细线性图标，桌面优先并自适应移动端。

---

## 功能一览

| 模块 | 说明 |
| --- | --- |
| 首页 | 日期与农历、本月收入/支出、总资产、今日与本周待办（可直接勾选）、随机笔记预览、六个快捷录入入口 |
| 待办 | 全部/今日/本周/已完成筛选、标签筛选、循环规则（日/周/月/年 + 结束日期）、完成时自动生成下一实例；每日三条系统待办（记账/锻炼/饮食），点击唤起快捷录入 |
| 日记 | 每天唯一一篇、打开即创建；标题按 ISO 周生成，如「2026年11月15日 46周星期日」；月历切换、自动保存、天气与心情 |
| 笔记 | Markdown 分栏编辑（左写右预览）、代码高亮与行号、标签与搜索、自动保存 |
| 健康 | 锻炼 / 饮食 / 体重 / 睡眠增删改；饮食内置离线食物库，按克数自动折算热量，可手动覆盖或自建食物；四类趋势图 |
| 娱乐 | 电影/电视剧/纪录片/播客/书籍，三列看板（想看/在看/看完）可拖拽换列，封面图上传、评分与进度 |
| 记账 | 多账户、收入/支出/转账，转账不计入收支；流水按月份/账户/分类筛选；总资产、分类环形图与近六月收支趋势 |
| 档案 | 个人信息、身份证脱敏展示（需再次输入口令才能看全文）、生肖星座与农历生日倒数、人生大事时间线 |

明确不支持：数学公式（KaTeX）与图表渲染（Mermaid）。

---

## 技术栈

- **后端**：Python 3.11.9（严格固定）、FastAPI、Uvicorn、SQLAlchemy 2.0 async + asyncpg、PostgreSQL 16、Alembic、Pydantic v2、PyJWT、argon2-cffi、APScheduler、lunar-python、cryptography、Pillow、pytest
- **前端**：Vue 3.5 + TypeScript + Vite 5、Vue Router 4、Pinia、Tailwind CSS 3.4、@tanstack/vue-query、markdown-it + highlight.js、CodeMirror 6、ECharts（按需注册）、vue-draggable-plus、vite-plugin-pwa
- **部署**：Docker Compose 四服务（web/nginx + api + postgres + backup），Nginx 负责 SPA fallback、gzip、静态长缓存、`/api` 反代、`/uploads` 直出、限流与安全响应头

---

## 目录结构

```
personal-workbench/
├── docker-compose.yml          # web / api / db / backup
├── .env.example                # 环境变量模板
├── deploy/
│   ├── Dockerfile.web          # 前端构建 + Nginx 托管
│   ├── nginx.conf              # 反代、缓存、限流、安全头
│   └── postgres.conf           # 2C2G 调优
├── scripts/
│   ├── backup.sh               # pg_dump -Fc，每日备份，保留 14 天
│   └── restore.sh              # 从备份恢复
├── backend/
│   ├── app/
│   │   ├── api/v1/             # auth/dashboard/todos/diaries/notes/foods/health/finance/entertainment/profile/upload/sync/meta
│   │   ├── core/               # 配置、鉴权、依赖、错误体、结构化日志
│   │   ├── db/                 # 引擎、Base、幂等种子与食物库 JSON
│   │   ├── models/             # SQLAlchemy 模型
│   │   ├── schemas/            # 请求与出参模型
│   │   └── services/           # ISO 周标题、农历、循环、热量折算、金额统计、加密、调度
│   ├── alembic/                # 首版迁移（含 pg_trgm 与部分唯一索引）
│   └── tests/                  # 核心算法单测
├── frontend/
│   └── src/
│       ├── views/              # 八个模块页面 + 登录 + 404
│       ├── components/         # 布局、UI、图表、Markdown、食物选择器、快捷录入
│       ├── api/                # axios 封装与全量类型
│       ├── composables/        # 日期/金额格式化、上传
│       └── router/             # 路由与登录守卫
└── tests/e2e/README.md         # 手工验收清单
```

---

## 快速开始（Docker，推荐）

前置：一台 2 核 2G 及以上的 Linux 服务器，已安装 Docker 与 Docker Compose 插件。

```bash
git clone <你的仓库地址> personal-workbench
cd personal-workbench

cp .env.example .env
# 修改下面四项，务必使用随机值
#   POSTGRES_PASSWORD  数据库口令
#   SECRET_KEY         openssl rand -hex 32
#   ADMIN_PASSWORD     首次登录口令（至少 8 位）
#   ID_CARD_KEY        openssl rand -base64 32（32 字节）

docker compose up -d --build
```

打开 `http://服务器IP`，输入 `ADMIN_PASSWORD` 进入。登录后可在「档案 → 修改口令」更换口令。

`api` 服务的 entrypoint 会在启动时自动执行 `alembic upgrade head` 与幂等种子（个人信息、默认记账分类与账户、139 条常用食物），重复启动不会产生重复数据。

### 常用命令

```bash
docker compose logs -f api      # 查看接口日志
docker compose ps               # 查看四个服务状态
docker compose restart api      # 重启接口（改了 .env 后）
docker compose down             # 停止（数据卷保留）
```

### 在 WSL2 里部署（Windows 本地）

WSL2 默认发行版（Ubuntu 24.04）里已带 Docker 时，可以直接复用本仓库部署，无需再装 Python 或 PostgreSQL：

```powershell
wsl -d Ubuntu-24.04
cd /mnt/d/Data/PersonalWorkspace
docker compose up -d --build
docker compose ps
```

- 打开 `http://localhost:8080`（WSL2 会把端口转发到 Windows）。仓库 `.env` 里已设置 `HTTP_PORT=8080`，避免和本机其他占用 80 端口的服务冲突；需要换端口改这一项即可。
- 如果 Docker Hub 拉取镜像失败，先在 `/etc/docker/daemon.json` 配置可用的 `registry-mirrors`，再 `sudo systemctl restart docker`。`nginx:1.27-alpine`、`node:20-alpine`、`python:3.11.9-slim` 三个基础镜像必须能拉到。
- 代码在 `/mnt/d` 下构建会比 WSL 原生文件系统慢；追求速度可把仓库复制到 `~/personal-workbench` 再构建，数据卷不受影响。
- 数据保存在 Docker 命名卷 `pwb_pgdata` 与 `pwb_uploads`，`docker compose down` 不会删除；需要彻底重置时执行 `docker compose down -v`（会丢数据，谨慎）。

---

## 部署到腾讯云轻量应用服务器

1. **购买与初始化**：选择 2 核 2G、Ubuntu 22.04 镜像，防火墙放行 80（以及后续的 443）。
2. **安装 Docker**：

   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER && newgrp docker
   ```

3. **拉取代码并配置**：

   ```bash
   git clone <你的仓库地址> ~/personal-workbench
   cd ~/personal-workbench
   cp .env.example .env && vim .env
   ```

   `.env` 中至少修改 `POSTGRES_PASSWORD`、`SECRET_KEY`、`ADMIN_PASSWORD`、`ID_CARD_KEY`。
   如果暂时用 IP 访问，保持 `COOKIE_SECURE=false`；启用 HTTPS 后改成 `true`。

4. **启动**：

   ```bash
   docker compose up -d --build
   docker compose logs -f api   # 看到迁移与种子完成后按 Ctrl+C 退出日志
   ```

5. **HTTPS（推荐）**：用 Caddy 或 Nginx 反代到 `127.0.0.1:80`，或直接用 Certbot 申请证书。

   ```bash
   sudo apt install -y certbot
   sudo certbot certonly --standalone -d your.domain.com
   ```

   然后在 `docker-compose.yml` 中把 `web` 的端口改为 `127.0.0.1:80:80`，由宿主机的 Nginx 终止 TLS 并反代；确认 HTTPS 正常后把 `.env` 的 `COOKIE_SECURE` 改为 `true` 并 `docker compose up -d`。

6. **PWA 安装**：手机浏览器打开站点，选择「添加到主屏幕」；桌面 Chrome/Edge 地址栏右侧会出现安装图标。

---

## 备份与恢复

`backup` 容器每天 02:00 执行 `pg_dump -Fc`，备份写入 `pwb_backups` 卷并保留 14 天。

```bash
# 手动备份
docker compose exec backup /bin/bash -c 'pg_dump -Fc -f /backups/manual-$(date +%F).dump'

# 导出到宿主机
docker compose cp backup:/backups ./backups

# 恢复到新实例（会覆盖现有数据库，务必确认）
docker compose stop api
docker compose cp ./backups/xxx.dump backup:/backups/restore.dump
docker compose exec backup /bin/bash /scripts/restore.sh /backups/restore.dump
docker compose start api
```

上传的图片在 `pwb_uploads` 卷中，重要节点可一并打包：`docker run --rm -v pwb_uploads:/data -v $PWD:/backup alpine tar czf /backup/uploads.tgz /data`。

---

## 忘记口令 / 重置口令

口令以 argon2 哈希存储，无法反推。重置方式：

```bash
docker compose exec api python - <<'PY'
import asyncio
from sqlalchemy import select
from app.core.security import hash_passcode
from app.db.session import async_session_factory
from app.models.auth import AuthCredential

async def main():
    async with async_session_factory() as session:
        cred = await session.scalar(select(AuthCredential).order_by(AuthCredential.id).limit(1))
        cred.passcode_hash = hash_passcode("新的口令至少8位")
        await session.commit()
        print("口令已重置")

asyncio.run(main())
PY
```

重置后旧 Cookie 仍会保持登录直到过期（默认 7 天），如需立即失效可清空浏览器 Cookie。

---

## 本地开发

### 后端（Python 3.11.9）

需要本机或容器中的 PostgreSQL 16（扩展 `pg_trgm` 由迁移自动创建）。

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://pwb:pwb_pass@127.0.0.1:5432/personal_workbench
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173，/api 与 /uploads 自动代理到 127.0.0.1:8000
npm run build      # 类型检查 + 产物构建
npm run test       # vitest
```

### 后端测试

```bash
cd backend
pytest -q
```

必须覆盖的核心口径：ISO 周标题（含跨年边界）、循环规则去重、转账不计入收支、系统待办幂等、热量折算与三路食物搜索。

---

## 关键口径说明

- **日记标题**：`{公历年}年{M}月{D}日 {ISO周}周{星期X}`，周号取 `date.isocalendar()`，不补零。跨年时年份用日期自身公历年、周号用 ISO 周号，例如 2027-01-01 为「2027年1月1日 53周星期五」。
- **金额**：数据库 `NUMERIC(14,2)`，后端全程 `Decimal`，接口返回字符串，统计在 SQL 内聚合，前端只做展示格式化。
- **账户余额** = 初始余额 + 收入 − 支出 + 转入 − 转出；转账不计入收入/支出。
- **系统待办**：`todo.system_key`（finance/exercise/diet）+ `UNIQUE(system_key, due_date)` 部分唯一索引保证幂等；每日 00:05 定时生成，接口访问时再兜底一次。
- **饮食热量**：`round(每100g热量 × 克数 / 100, 1)`，以快照写在记录上，之后修正食物库不会影响历史记录。
- **身份证**：AES-256-GCM 加密存密文，另存 `id_card_masked`（前 6 后 4）用于列表；查看全文需再次校验口令，票据 5 分钟有效。

---

## 食物库数据说明

内置 139 条日常高频食物（谷薯主食、肉禽蛋、水产、奶豆、蔬果、坚果、家常菜、饮品），字段参考《中国食物成分表（第 6 版）》的公开营养数据整理，仅用于个人估算，不作为医疗或营养学依据。

- 数据以静态 JSON 随代码分发，导入本地数据库，**断网可用，不上传任何饮食数据到外部服务**。
- 不承诺覆盖全部食物，长尾食物请使用「新建食物」补充。
- 系统内置食物不可修改或删除（接口返回 403）；自定义食物可改可删。

---

## 安全与运维要点

- 登录使用 HttpOnly + SameSite=Lax Cookie 承载 JWT；写操作要求 `X-Requested-With` 头，配合 JSON-only 请求抵御 CSRF。
- 登录失败按 IP 限流：15 分钟内 5 次；Nginx 对 `/api/v1/auth/login` 另有一层 6 次/分钟限流。
- Nginx 注入 CSP、`X-Content-Type-Options`、`Referrer-Policy`、`Permissions-Policy`。
- 上传校验 MIME 与文件魔数双重白名单，重命名存储，统一转 WebP 并生成 400px 缩略图，防止路径穿越。
- 日志为结构化 JSON（request_id、路由、耗时、状态码），不记录口令、身份证明文与完整 token。

---

## 已知限制

- 不支持数学公式与图表渲染（需求明确排除），Markdown 中的 `$$`、`mermaid` 会按普通文本显示。
- 多端同步为服务端单一数据源 + 查询失效刷新，不做离线双向合并；离线时仅能打开已缓存的界面外壳。
- 记账暂不支持分期、预算与多币种换算。
- 备份为整库快照，单条记录误删需从最近备份恢复。

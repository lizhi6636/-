# 量化学习平台 (Quant Trading Learning Platform)

全栈量化交易学习平台 — 集实时行情、模拟交易、策略回测、因子挖掘、量化知识库于一体。

**技术栈**: React + TypeScript + FastAPI + PostgreSQL + Redis + Celery + Docker

---

## 项目亮点

- **自研模拟交易引擎**：支持市价单/限价单、T+1 约束、手续费/印花税计算、交易时间感知，所有数据持久化到 PostgreSQL
- **多数据源容错架构**：EastMoney API 多端点回退 + Redis 缓存 + WebSocket 推送，确保行情数据高可用
- **JWT 双 Token 认证**：access_token（30min）+ refresh_token（最长30天），支持记住登录、静默刷新
- **全 Docker 化部署**：6 个容器一键启动（前端/后端/PostgreSQL/Redis/Celery Worker/Celery Beat）
- **120+ 源文件**，前后端分离架构，TypeScript 类型安全，RESTful API 设计

---

## 系统架构

```
用户浏览器 (React + Ant Design)
       ↓ HTTP / WebSocket
  Vite Dev Server (代理)
       ↓
  FastAPI 应用服务
   ├── 用户认证 (JWT 双 Token)
   ├── 实时行情 (EastMoney + Redis 缓存)
   ├── 模拟交易引擎 (撮合/T+1/手续费)
   ├── 回测任务管理 (Celery 异步)
   └── 因子挖掘服务
       ↓
  Celery Worker (后台异步任务)
   ├── 数据抓取 & 清洗
   ├── 回测计算
   └── 因子计算 & 评测
       ↓
  PostgreSQL (用户/持仓/订单/策略)  +  Redis (行情缓存/任务队列)
```

---

## 功能模块

| 模块 | 路由 | 功能 |
|------|------|------|
| 仪表盘 | `/` | 三大指数实时、自选股行情、账户概览、权益曲线 |
| 个股详情 | `/stock/:code` | K线图、分时数据、基本信息、一键跳转东方财富 |
| 模拟交易 | `/simulation` | 下单面板、持仓盈亏、委托记录、T+1约束、手续费计算 |
| 策略回测 | `/backtest` | 策略配置、异步回测任务、结果展示 |
| 因子挖掘 | `/factor` | 因子库浏览、自定义因子计算、因子分析 |
| 量化学院 | `/learn` | 知识库文章、策略案例、API文档 |

---

## 技术栈详解

| 层级 | 技术 | 选型理由 |
|------|------|----------|
| 前端框架 | React 18 + TypeScript | 组件化强、类型安全、生态丰富 |
| UI 组件库 | Ant Design 5 | 企业级数据看板组件 |
| 图表 | ECharts 5 | K线图、权益曲线、因子分布图 |
| 状态管理 | Zustand | 轻量级、无模板代码 |
| 编辑器 | Monaco Editor | 策略代码在线编辑 |
| 后端框架 | FastAPI (Python 3.12) | 异步高性能、自动 API 文档、原生对接量化库 |
| 数据库 | PostgreSQL 16 | ACID 事务、复杂查询、数据完整性 |
| 缓存 | Redis 7 | 实时行情缓存、任务队列、会话管理 |
| 异步任务 | Celery + Redis | 回测/因子计算异步执行、定时任务调度 |
| 认证 | JWT (python-jose) | 无状态认证，access + refresh 双 Token |
| 行情数据 | EastMoney API | 免费实时行情，多端点容错，curl 调用绕过 TLS 限制 |
| 容器化 | Docker Compose | 6 服务编排，一键部署，环境隔离 |
| 代码编辑器 | Monaco Editor | VS Code 内核，支持 Python 语法高亮 |

---

## 快速开始

### 环境要求

- Docker Desktop
- Node.js 18+（本地开发）
- Python 3.12+（本地开发）

### 一键启动（Docker）

```bash
# 1. 克隆仓库
git clone git@github.com:lizhi6636/-.git
cd -  # 或 cd 量化网站

# 2. 复制环境配置（填入你的密钥）
cp .env.example .env

# 3. 启动所有服务
docker compose -p quant up -d

# 4. 访问
# 前端: http://localhost:3000
# 后端 API 文档: http://localhost:8000/docs
# 测试账号: test@test.com / test123
```

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev  # http://localhost:5173
# 注意: 本地开发需将 vite.config.ts 中代理目标改为 http://localhost:8000

# 基础设施
docker compose -p quant up -d postgres redis
```

---

## 项目结构

```
量化网站/
├── frontend/                     # React 前端
│   ├── src/
│   │   ├── api/                  # API 请求层 (axios 封装)
│   │   ├── components/           # 通用组件
│   │   │   ├── charts/           # K线图、权益曲线
│   │   │   ├── Layout/           # 应用布局、侧边菜单
│   │   │   └── trading/          # 交易组件（刷新选择器等）
│   │   ├── hooks/                # 自定义 Hook (usePolling, useWebSocket)
│   │   ├── pages/                # 页面组件
│   │   │   ├── Dashboard/        # 仪表盘
│   │   │   ├── Simulation/       # 模拟交易
│   │   │   ├── Backtest/         # 策略回测
│   │   │   ├── Factor/           # 因子挖掘
│   │   │   ├── StockDetail/      # 个股详情
│   │   │   ├── Learn/            # 量化学院
│   │   │   └── Login/            # 登录注册
│   │   ├── store/                # Zustand 状态管理
│   │   ├── types/                # TypeScript 类型定义
│   │   └── utils/                # 工具函数
│   ├── vite.config.ts            # Vite 配置（含 API 代理）
│   └── Dockerfile
│
├── backend/                      # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/               # API 路由
│   │   │   ├── auth.py           # 认证接口
│   │   │   ├── simulation.py     # 模拟交易接口
│   │   │   ├── market_data.py    # 行情数据接口
│   │   │   ├── backtest.py       # 回测接口
│   │   │   ├── factor.py         # 因子接口
│   │   │   ├── dashboard.py      # 仪表盘接口
│   │   │   └── stocks.py         # 个股接口
│   │   ├── core/                 # 核心模块
│   │   │   ├── security.py       # JWT + 密码哈希
│   │   │   ├── database.py       # 异步 SQLAlchemy
│   │   │   ├── redis_client.py   # Redis 客户端
│   │   │   └── celery_app.py     # Celery 配置
│   │   ├── models/               # ORM 模型 (9张表)
│   │   ├── schemas/              # Pydantic 验证模型
│   │   ├── services/             # 业务逻辑层
│   │   │   ├── simulation_engine.py  # 模拟交易引擎（核心）
│   │   │   ├── market_data_service.py # 行情服务（多端点容错）
│   │   │   ├── dashboard_service.py   # 仪表盘聚合
│   │   │   ├── auth_service.py        # 认证服务
│   │   │   ├── backtest_service.py    # 回测服务
│   │   │   └── factor_service.py      # 因子服务
│   │   └── ws/                   # WebSocket 实时推送
│   ├── alembic/                  # 数据库迁移
│   └── Dockerfile
│
├── docker-compose.yml            # 6 服务编排
├── .env.example                  # 环境变量模板
├── .gitignore                    # Git 忽略规则
└── README.md                     # 本文档
```

---

## 数据库设计

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| users | 用户 | email, username, hashed_password, cash |
| positions | 持仓 | stock_code, quantity, avg_cost, current_price |
| orders | 订单 | stock_code, direction, order_type, status |
| trades | 成交 | order_id, price, quantity, commission |
| account_snapshots | 每日快照 | total_asset, total_pnl, snapshot_time |
| backtest_tasks | 回测任务 | strategy_name, params, status, result_json |
| factor_definitions | 因子定义 | name, expression, category |
| watchlist_items | 自选股 | stock_code, stock_name, sort_order |
| learn_articles | 知识文章 | title, category, content, tags |

---

## 模拟交易引擎特性

- **订单类型**: 市价单（即时成交）、限价单（价格触发）
- **撮合规则**: 市价单以实时行情立即成交；限价单待行情达到限价后触发
- **T+1 约束**: 当日买入股票不可当日卖出（available_quantity 与 quantity 分离）
- **手续费模型**: 佣金万2.5（最低5元）+ 卖出印花税千1
- **资金冻结**: 限价买单预先冻结资金，撤单释放
- **交易时间**: 真实 A 股交易时间感知（9:30-11:30, 13:00-15:00）
- **数据持久化**: 所有订单/成交/持仓即时写入 PostgreSQL，关闭浏览器不丢失

---

## 行情数据方案

采用多端点容错架构解决 Python TLS + Docker 网络问题：

```
请求行情 → 查 Redis 缓存 → 命中: 直接返回
              ↓ 未命中
         curl 调用 push2delay.eastmoney.com (HTTP) → 成功: 缓存并返回
              ↓ 失败
         curl 调用 push2.eastmoney.com (HTTP) → 成功: 缓存并返回
              ↓ 全部失败
         返回空，前端使用上次缓存数据（不显示成本价）
```

支持沪深北三大交易所 6000+ 股票实时行情，缓存 TTL 5 秒。

---

## 部署架构

```
Docker Compose 6 服务:
┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────┐  ┌───────────────┐
│ frontend │  │ backend  │  │ postgres  │  │ redis        │  │ celery_worker │
│ :3000    │  │ :8000    │  │ :5432     │  │ :6379        │  │               │
│ Vite+React│  │ FastAPI  │  │ PG 16     │  │ Redis 7      │  │ 异步任务      │
└──────────┘  └──────────┘  └───────────┘  └──────────────┘  └───────────────┘
                                                                    │
                                                           ┌───────────────┐
                                                           │ celery_beat   │
                                                           │ 定时任务调度   │
                                                           └───────────────┘
```

---

## API 文档

启动后访问 `http://localhost:8000/docs` 查看 Swagger UI 自动生成的完整 API 文档。

主要接口：
- `POST /api/v1/auth/login` — 用户登录
- `POST /api/v1/auth/register` — 用户注册
- `GET /api/v1/market/quotes?codes=...` — 实时行情
- `GET /api/v1/market/indices` — 三大指数
- `POST /api/v1/simulation/orders` — 下单
- `GET /api/v1/simulation/positions` — 持仓查询
- `GET /api/v1/dashboard/overview` — 仪表盘聚合
- `POST /api/v1/backtest/tasks` — 提交回测任务

---

## License

MIT

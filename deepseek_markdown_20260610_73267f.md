# 量化学习网站框架设计文档

> **目标**：构建一个集量化知识学习、股票数据查询、回测、因子挖掘与模拟交易于一体的全栈Web平台。  
> **核心用户**：量化初学者、股票交易爱好者。  
> **核心理念**：低门槛使用，数据实时可配，模拟交易状态永久保存，关键操作可一键跳转专业工具。

---

## 1. 技术栈选型

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | React + TypeScript + Ant Design / TDesign | 组件化强，生态丰富，适合数据看板 |
| 图表 | ECharts / TradingView Lightweight Charts | K线图、因子分布图、回测曲线 |
| 后端 | Python FastAPI | 异步高性能，天然对接量化库 |
| 数据库 | PostgreSQL + Redis | PG存业务数据，Redis缓存实时行情与任务状态 |
| 消息队列 | Celery + Redis | 异步执行回测、因子计算、数据抓取 |
| 回测引擎 | Backtrader / Zipline-Reloaded | 成熟稳定，可扩展 |
| 因子工具 | Alphalens + 自定义因子模块 | 因子分析、IC分析、分层回测 |
| 实时行情 | AKShare + EastMoney Websocket + 模拟点击备选 | 详见第5节 |
| 部署 | Docker + Nginx + Gunicorn | 统一环境，易于扩展 |

---

## 2. 系统架构概览

```
用户浏览器 (React)
       ↓ HTTP / WebSocket
Nginx 反向代理
       ↓
FastAPI 应用服务
   ├── 用户认证 (JWT)
   ├── 行情路由 (实时+历史)
   ├── 模拟交易引擎
   ├── 回测任务管理
   └── 因子挖掘服务
       ↓
Celery Worker (后台任务)
   ├── 数据抓取 & 清洗
   ├── 回测计算
   └── 因子计算 & 评测
       ↓
PostgreSQL (用户数据、持仓、订单、策略、因子库)
Redis (行情缓存、任务队列、模拟账户快照)
```

---

## 3. 前端功能模块设计

### 3.1 页面路由

- `/` 仪表盘：市场概览、自选股实时、模拟账户摘要
- `/stock/:code` 个股详情：K线、分时、基本信息、一键跳转
- `/backtest` 回测工作台：策略配置、结果展示、归因分析
- `/factor` 因子挖掘：因子库浏览、自定义因子计算、因子分析
- `/simulation` 模拟交易：下单面板、持仓、委托、成交记录
- `/learn` 量化学院：知识库、策略案例、API文档

### 3.2 关键交互

#### a) 数据刷新时间选择
在仪表盘和个股页顶部放置刷新间隔选择器：
- 选项：`实时(WebSocket推送)`、`5秒`、`15秒`、`30秒`、`1分钟`、`手动刷新`
- 实现：前端维护一个下拉按钮，切换后改变轮询间隔或重新订阅WebSocket频道。后端支持对应粒度的数据推送。

#### b) 一键跳转股票软件
在个股详情页和自选股列表旁提供 **“外部软件”** 按钮组：
- 配置：`https://stockpage.10jqka.com.cn/{code}/` (同花顺网页版)
- 或使用URL Scheme打开本地App：`ths://stock?code={code}`（若用户已安装同花顺App）
- 安卓/iOS判断：前端通过 `navigator.userAgent` 判断平台，动态生成链接。
- 跳转按钮可下拉选择：同花顺网页、东方财富网页、同花顺App、雪球App等。

#### c) 模拟交易界面
- 交易面板：股票代码输入、买卖方向、价格类型（限价/市价）、数量、可用资金显示
- 实时持仓：浮动盈亏、仓位占比
- 委托记录：状态标签（已报、部成、已成、已撤）
- 成交记录：时间、价格、数量、手续费

---

## 4. 后端核心服务

### 4.1 用户系统
- 注册/登录（JWT + 邮箱验证）
- 账户余额管理（模拟资金初始化100万）
- 每个用户独立持仓、订单、策略空间

### 4.2 模拟交易引擎（核心）
- 撮合规则：
  - 限价单：按行情逐笔检查，达到价位即成交。
  - 市价单：以当前最新价立即成交（简化模型）。
- 手续费：万2.5，印花税千1（卖出），最低5元。
- 持仓计算：买入增加持仓，卖出扣减，支持T+1检查（可配置开关）。
- **数据持久化**：所有订单、成交、持仓、账户余额实时写入PostgreSQL，并每日快照存入Redis以防丢失。关闭浏览器/重启服务后数据不丢失。

### 4.3 回测引擎
- 基于Backtrader封装：
  - 支持多股票、多周期回测。
  - 用户上传Python策略代码或在线编辑。
  - 后端用沙箱执行，限制CPU/内存。
- 回测结果：
  - 权益曲线、年化收益、最大回撤、夏普比率等指标。
  - 交易明细导出。
- 任务管理：Celery异步执行，返回进度与结果URL，存入数据库与用户关联。

### 4.4 因子挖掘模块
- 因子库：预制常见因子（PE、PB、ROE、动量、波动率、换手率等），提供因子表达式编辑器。
- 用户自定义因子：支持类Python表达式，后端解析并用Pandas计算。
- 因子分析：基于Alphalens输出IC序列、分层收益、因子自相关等图表。

---

## 5. 股票实时数据接口方案

### 5.1 首选稳定方案
**AKShare + 东方财富Websocket**
- 历史日线、分钟线通过AKShare的`stock_zh_a_hist`等接口获取，免费无限制。
- 实时行情：东方财富Websocket推送，字段丰富，可用于实时K线更新。

**实现路径**：
1. 后端启动WebSocket客户端连接东方财富，订阅全市场或自选股。
2. 将行情流解析后通过Redis Pub/Sub分发。
3. FastAPI通过WebSocket转发给前端，前端按刷新间隔展示。
4. 若无实时要求，前端可轮询后端的缓存数据（已由后台任务实时更新Redis）。

### 5.2 模拟交易时间显示与接口限制规避
部分交易接口（如券商API）有严格认证和时间限制。对于纯学习性质网站，我们**不接入真实券商交易接口**，而是构造一个虚拟的交易环境，但提供真实的交易时间体验：

- **显示当前交易状态**：日历判断交易日，盘中时段（9:30-11:30, 13:00-15:00）标记为“交易中”，其余为“已收盘”。后端维护一个全局的“虚拟时钟”，在盘中按照真实时间推进，供模拟交易撮合使用。
- **模拟点击规避限制**（备选方案，用于获取免费延时数据）：
  若需获取类似同花顺level-2的深度数据且不想受频率限制，可使用**Playwright**自动化工具模拟人工操作：
  - 在服务器上用`playwright-python`启动无头浏览器，打开同花顺网页版或公共行情站点。
  - 定时移动鼠标、随机滚动，模拟人类行为。
  - 通过`page.evaluate()`或`page.wait_for_selector()`抓取DOM中的数据。
  - 这种方式仅用于数据采集，严格遵守robots.txt及合理使用原则，并设置较长的间隔（如3-5秒刷新一次），避免对目标站点造成压力。**推荐仅在私有学习环境下使用，生产环境必须改用正规数据源。**
- 更稳妥的建议：直接引导用户自行申请免费数据API（如Tushare Pro积分足够免费，聚宽数据SDK等），网站集成调用。

---

## 6. 模拟交易数据持久化模型

### 6.1 数据库表设计（PostgreSQL）
- `users`：id, username, password_hash, email, cash_balance, created_at
- `positions`：id, user_id, stock_code, volume, avg_cost, updated_at
- `orders`：id, user_id, stock_code, direction(BUY/SELL), price_type(LIMIT/MARKET), limit_price, volume, filled_volume, status, created_at, updated_at
- `trades`：id, order_id, user_id, stock_code, price, volume, trade_time
- `account_snapshots`：id, user_id, date, total_value, cash, market_value, pnl (每日结算快照)
- `backtest_tasks`：id, user_id, strategy_name, params, status, result_json, created_at
- `factor_definitions`：id, user_id, name, expression, created_at

### 6.2 持久化策略
- 任何交易操作均在事务中完成：锁用户行，检查资金/持仓，写入订单，若有成交即时写入trade并更新position和cash。
- 页面关闭重开后，前端请求`/api/account`、`/api/positions`、`/api/orders?status=active`即可恢复全部状态。
- 定期结算每日净值，存入`account_snapshots`，用于绘制账户权益曲线。

---

## 7. 刷新时间按键实现细节

### 7.1 前端逻辑
1. 定义一个 `RefreshInterval` 状态，默认 `'realtime'`。
2. 当选中具体秒数，启动 `setInterval` 调用数据获取API；切换回“实时”则切换到WebSocket模式。
3. 刷新按钮旁显示距离下次刷新的倒计时（可选）。

### 7.2 后端支持
- `/api/market/quotes?codes=...` 返回Redis缓存的最新价。
- WebSocket接口：`ws://domain/ws/market`，客户端发送订阅消息，服务端根据Redis流实时推送。

---

## 8. 一键跳转股票网站实现

在React组件中：

```tsx
const code = '000001'; // 或者从props获取
const jumpUrls = {
  tonghuashun_web: `https://stockpage.10jqka.com.cn/${code}/`,
  eastmoney_web: `https://quote.eastmoney.com/sz${code}.html`,
  tonghuashun_app: `ths://stock?code=${code}`,
  xueqiu_app: `xueqiu://stock/${code}`,
};
// 点击按钮时：
window.open(jumpUrls.tonghuashun_web, '_blank');
// 尝试打开app (移动端)
if (/Android|iPhone/.test(navigator.userAgent)) {
  window.location.href = jumpUrls.tonghuashun_app;
}
```

可封装为 `ExternalStockLink` 组件。

---

## 9. 交易接口时间显示与虚拟时钟

### 9.1 虚拟交易时间逻辑
- 后端任务每分钟检查实际时间，生成 `TradingTime` 对象：`{isTrading: bool, session: "morning"|"afternoon"|null, next_open: datetime}`。
- 模拟交易撮合只在 `isTrading=True` 时触发；否则订单挂起至开盘。
- 前端展示“当前状态：交易中（上午盘）”或“已收盘，距下次开盘xx:xx:xx”。

### 9.2 模拟点击避免限制（技术探讨）
如果决定使用前端自动化获取数据，可以采用以下架构：
- 独立容器运行 Playwright 脚本，每N秒访问目标页面，提取股票报价。
- 通过API将数据写入Redis，供主后端调用。
- 风险提示：容易因页面改版而失效，且违反部分网站条款。本框架**仅作为技术说明**，正式环境中强烈建议采用合法合规的数据源。

---

## 10. 开发与部署指导

### 10.1 本地开发环境
- 后端：`uvicorn main:app --reload`
- 前端：`npm run dev`（Vite）
- Celery worker：`celery -A app.celery worker --loglevel=info`
- Redis、PostgreSQL用Docker Compose启动。

### 10.2 Docker部署
提供 `docker-compose.yml`，包含所有服务。前端构建后由Nginx提供静态文件，API通过反向代理。

### 10.3 给AI的编码指引
1. **前后端分离**，RESTful API设计，所有API文档自动生成（FastAPI自带）。
2. **数据库迁移**使用Alembic，首次运行自动创建表。
3. **模拟交易撮合**抽离为独立模块，单元测试覆盖各种订单状态。
4. **行情服务**采用策略模式设计，方便切换数据源（AKShare -> 东方财富WS -> 自定义爬虫）。
5. **安全考虑**：用户策略代码在Docker沙箱中执行，防止恶意代码影响主机。
6. **扩展性**：因子计算模块支持插件式注册新因子。

---

## 11. 总结

本框架详细规划了一个量化学习全栈网站，涵盖了前端交互、后端服务、数据工程与持久化等关键环节。特别针对**实时数据刷新可选**、**股票一键跳转**、**模拟交易持久化**及**交易时间感知**进行了定制设计。在数据源部分，主推合法合规的开放API，同时给出了模拟点击的技术探讨供技术验证，但建议开发者最终选择正规途径。按照此文档的结构和技术选型，AI可以逐步生成可运行的代码库，快速搭建出功能完善的量化学习平台。
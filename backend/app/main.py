"""Quantitative Trading Learning Platform — FastAPI Application."""

import logging
import sys
from contextlib import asynccontextmanager

# Fix for Windows ProactorEventLoop + Docker port forwarding issue
if sys.platform == "win32":
    import asyncio
    try:
        from asyncio import WindowsSelectorEventLoopPolicy
        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    except ImportError:
        pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.v1.router import api_router
from app.ws.router import ws_router
from app.core.database import engine, Base

# Import all models so they are registered on Base.metadata
from app.models import *  # noqa: F401, F403

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Startup
    logger.info("Starting Quant Trading Platform...")

    # Create tables (for development; use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed system factors
    try:
        from app.core.database import async_session
        from app.services.factor_service import seed_system_factors
        async with async_session() as db:
            await seed_system_factors(db)
            logger.info("System factors seeded")
    except Exception as e:
        logger.warning(f"Could not seed system factors (DB may not be ready): {e}")

    # Seed sample learn articles
    try:
        from app.core.database import async_session
        from app.models.learn_article import LearnArticle
        from sqlalchemy import select
        async with async_session() as db:
            result = await db.execute(select(LearnArticle).limit(1))
            if result.scalar_one_or_none() is None:
                sample_articles = [
                    LearnArticle(
                        title="量化交易入门指南",
                        category="knowledge",
                        summary="了解量化交易的基本概念、常用策略和实施流程",
                        content="""# 量化交易入门指南

## 什么是量化交易？

量化交易是指利用数学模型、统计分析和计算机程序来制定交易策略的方法。

## 核心要素

1. **数据** — 历史行情、财务数据、宏观经济指标
2. **策略** — 基于规则的买卖决策逻辑
3. **执行** — 自动化订单下达和风险控制
4. **评估** — 回测验证和实盘跟踪

## 常用策略类型

- **趋势跟踪**：移动平均线交叉、通道突破
- **均值回归**：布林带、RSI超买超卖
- **统计套利**：配对交易、协整关系
- **因子投资**：多因子选股模型

## 学习路径

1. 掌握Python编程基础
2. 学习金融市场基础知识
3. 了解常见技术指标
4. 通过回测验证策略
5. 模拟交易积累经验
""",
                        tags=["入门", "基础", "量化"],
                    ),
                    LearnArticle(
                        title="Backtrader策略开发实战",
                        category="case",
                        summary="使用Backtrader框架开发和回测一个双均线交叉策略",
                        content="""# Backtrader双均线策略实战

## 策略逻辑

当短期均线上穿长期均线时买入，下穿时卖出。

## 完整代码

```python
import backtrader as bt

class MACrossover(bt.Strategy):
    params = (
        ('fast', 10),
        ('slow', 30),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(
            self.data.close, period=self.params.fast
        )
        self.slow_ma = bt.indicators.SMA(
            self.data.close, period=self.params.slow
        )
        self.crossover = bt.indicators.CrossOver(
            self.fast_ma, self.slow_ma
        )

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.sell()
```

## 参数优化

- fast: 5, 10, 20, 30
- slow: 20, 30, 60, 120

## 注意事项

1. 双均线策略在震荡市中容易产生假信号
2. 建议配合止损使用
3. 不同市场和周期效果差异大
""",
                        tags=["Backtrader", "策略", "均线"],
                    ),
                    LearnArticle(
                        title="API接口使用文档",
                        category="api",
                        summary="本平台所有API接口的使用说明和示例",
                        content="""# API接口文档

## 认证

所有API请求（除注册/登录外）需在Header中携带JWT Token：

```
Authorization: Bearer <access_token>
```

## 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/register | 用户注册 |
| POST | /api/v1/auth/login | 用户登录 |
| GET | /api/v1/auth/me | 获取当前用户信息 |
| GET | /api/v1/stocks/{code}/kline | 获取K线数据 |
| GET | /api/v1/market/indices | 获取主要指数 |
| POST | /api/v1/simulation/orders | 下单 |
| GET | /api/v1/simulation/positions | 查询持仓 |
| POST | /api/v1/backtest/tasks | 提交回测任务 |

完整文档请访问 `/docs` 查看Swagger UI。
""",
                        tags=["API", "文档"],
                    ),
                ]
                for article in sample_articles:
                    db.add(article)
                await db.commit()
                logger.info("Sample learn articles seeded")
    except Exception as e:
        logger.warning(f"Could not seed articles: {e}")

    # Start EastMoney WebSocket client (optional, in background)
    # try:
    #     from app.ws.eastmoney import eastmoney_client
    #     eastmoney_client.start()
    # except Exception as e:
    #     logger.warning(f"EastMoney client not started: {e}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    # from app.ws.eastmoney import eastmoney_client
    # eastmoney_client.stop()
    from app.core.redis_client import close_redis
    await close_redis()


app = FastAPI(
    title="量化学习平台",
    description="集量化知识学习、股票数据查询、回测、因子挖掘与模拟交易于一体的全栈Web平台",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)
app.include_router(ws_router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "code": "internal_error"},
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

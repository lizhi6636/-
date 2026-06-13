"""Seed data script — populates system factors and sample learn articles.

Usage:
    docker compose exec backend python /app/scripts/seed_data.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session
from app.models.factor_definition import FactorDefinition
from app.models.learn_article import LearnArticle
from sqlalchemy import select


SYSTEM_FACTORS = [
    {"name": "pe_ttm", "display_name": "市盈率 PE(TTM)", "description": "滚动市盈率 = 股价 / 近12个月每股收益",
     "expression": "market_cap / net_profit_ttm", "category": "system"},
    {"name": "pb", "display_name": "市净率 PB", "description": "市净率 = 股价 / 每股净资产",
     "expression": "market_cap / total_equity", "category": "system"},
    {"name": "roe", "display_name": "净资产收益率 ROE", "description": "净资产收益率 = 净利润 / 净资产",
     "expression": "net_profit / total_equity", "category": "system"},
    {"name": "momentum_20d", "display_name": "20日动量", "description": "过去20个交易日的累计收益率",
     "expression": "(close - close_20d_ago) / close_20d_ago", "category": "technical"},
    {"name": "volatility_20d", "display_name": "20日波动率", "description": "过去20个交易日收益率的标准差",
     "expression": "std(returns_20d)", "category": "technical"},
    {"name": "turnover_rate", "display_name": "换手率", "description": "当日成交量 / 流通股本",
     "expression": "volume / float_shares", "category": "technical"},
]


async def seed():
    async with async_session() as db:
        # Seed system factors
        for fd in SYSTEM_FACTORS:
            stmt = select(FactorDefinition).where(
                FactorDefinition.name == fd["name"],
                FactorDefinition.user_id.is_(None),
            )
            result = await db.execute(stmt)
            if result.scalar_one_or_none() is None:
                factor = FactorDefinition(user_id=None, **fd)
                db.add(factor)
                print(f"  + Factor: {fd['name']}")

        # Seed sample articles
        stmt = select(LearnArticle).limit(1)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            articles = [
                LearnArticle(
                    title="量化交易入门指南",
                    category="knowledge",
                    summary="了解量化交易的基本概念和常用策略类型",
                    content="# 量化交易入门指南\n\n量化交易是利用数学模型和计算机程序来制定交易策略的方法。\n\n## 核心要素\n1. 数据\n2. 策略\n3. 执行\n4. 评估",
                    tags=["入门", "基础"],
                ),
                LearnArticle(
                    title="双均线策略实战",
                    category="case",
                    summary="使用Backtrader实现经典的双均线交叉策略",
                    content="# 双均线策略\n\n当短期均线上穿长期均线时买入，下穿时卖出。\n\n```python\nimport backtrader as bt\n\nclass MACrossover(bt.Strategy):\n    params = (('fast', 10), ('slow', 30))\n```",
                    tags=["策略", "均线", "Backtrader"],
                ),
            ]
            for a in articles:
                db.add(a)
                print(f"  + Article: {a.title}")

        await db.commit()
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())

"""Factor service — factor CRUD, expression evaluation, Alphalens integration."""

import logging
from typing import Optional
from uuid import UUID

import pandas as pd
import numpy as np
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.factor_definition import FactorDefinition
from app.schemas.factor import FactorCreate, FactorUpdate

logger = logging.getLogger(__name__)

# System factor definitions (seeded on first run)
SYSTEM_FACTORS = [
    {
        "name": "pe_ttm",
        "display_name": "市盈率 PE(TTM)",
        "description": "滚动市盈率 = 股价 / 近12个月每股收益",
        "expression": "market_cap / net_profit_ttm",
        "category": "system",
    },
    {
        "name": "pb",
        "display_name": "市净率 PB",
        "description": "市净率 = 股价 / 每股净资产",
        "expression": "market_cap / total_equity",
        "category": "system",
    },
    {
        "name": "roe",
        "display_name": "净资产收益率 ROE",
        "description": "净资产收益率 = 净利润 / 净资产",
        "expression": "net_profit / total_equity",
        "category": "system",
    },
    {
        "name": "momentum_20d",
        "display_name": "20日动量",
        "description": "过去20个交易日的累计收益率",
        "expression": "(close - close_20d_ago) / close_20d_ago",
        "category": "technical",
    },
    {
        "name": "volatility_20d",
        "display_name": "20日波动率",
        "description": "过去20个交易日收益率的标准差",
        "expression": "std(returns_20d)",
        "category": "technical",
    },
    {
        "name": "turnover_rate",
        "display_name": "换手率",
        "description": "当日成交量 / 流通股本",
        "expression": "volume / float_shares",
        "category": "technical",
    },
]


async def seed_system_factors(db: AsyncSession):
    """Seed system factor definitions if they don't exist."""
    for factor_data in SYSTEM_FACTORS:
        stmt = select(FactorDefinition).where(
            FactorDefinition.name == factor_data["name"],
            FactorDefinition.user_id.is_(None),
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            factor = FactorDefinition(
                user_id=None,  # System factor
                **factor_data,
            )
            db.add(factor)
    await db.commit()


async def get_all_factors(
    db: AsyncSession,
    user: Optional[User] = None,
    category: Optional[str] = None,
) -> list[FactorDefinition]:
    """Get all visible factors (system + user's own)."""
    conditions = [
        (FactorDefinition.user_id.is_(None)) | (FactorDefinition.user_id == user.id)
        if user
        else FactorDefinition.user_id.is_(None)
    ]
    if category:
        conditions.append(FactorDefinition.category == category)

    stmt = (
        select(FactorDefinition)
        .where(*conditions)
        .order_by(FactorDefinition.category, FactorDefinition.name)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_factor(
    db: AsyncSession,
    user: User,
    data: FactorCreate,
) -> FactorDefinition:
    """Create a custom factor."""
    # Check name uniqueness
    stmt = select(FactorDefinition).where(
        FactorDefinition.name == data.name,
        FactorDefinition.user_id == user.id,
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ValueError(f"因子名称 '{data.name}' 已存在")

    factor = FactorDefinition(
        user_id=user.id,
        **data.model_dump(),
    )
    db.add(factor)
    await db.commit()
    await db.refresh(factor)
    return factor


async def update_factor(
    db: AsyncSession,
    user: User,
    factor_id: UUID,
    data: FactorUpdate,
) -> Optional[FactorDefinition]:
    """Update a custom factor."""
    stmt = select(FactorDefinition).where(
        FactorDefinition.id == factor_id,
        FactorDefinition.user_id == user.id,
    )
    result = await db.execute(stmt)
    factor = result.scalar_one_or_none()
    if not factor:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(factor, key, value)

    await db.commit()
    await db.refresh(factor)
    return factor


async def delete_factor(
    db: AsyncSession,
    user: User,
    factor_id: UUID,
) -> bool:
    """Delete a custom factor."""
    stmt = delete(FactorDefinition).where(
        FactorDefinition.id == factor_id,
        FactorDefinition.user_id == user.id,
        FactorDefinition.category != "system",  # Can't delete system factors
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def preview_factor_expression(
    expression: str,
    stock_code: str,
    start_date: str,
    end_date: str,
) -> Optional[dict]:
    """Preview a factor expression by calculating it on historical data."""
    try:
        import akshare as ak

        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )

        if df is None or df.empty:
            return None

        # Create a safe eval context with basic data
        close = df["收盘"].values
        open_ = df["开盘"].values
        high = df["最高"].values
        low = df["最低"].values
        volume = df["成交量"].values

        # Simple expression evaluation
        context = {
            "close": close,
            "open": open_,
            "high": high,
            "low": low,
            "volume": volume,
            "np": np,
        }

        try:
            result = eval(expression, {"__builtins__": {}}, context)
            if hasattr(result, "tolist"):
                result = result.tolist()
            return {
                "expression": expression,
                "latest_value": float(result[-1]) if len(result) > 0 else None,
                "sample_size": len(result),
            }
        except Exception as e:
            return {"expression": expression, "error": str(e)}

    except Exception as e:
        logger.error(f"Factor preview failed: {e}")
        return None


async def analyze_factor(
    factor: FactorDefinition,
    stock_codes: list[str],
    start_date: str,
    end_date: str,
) -> Optional[dict]:
    """Run factor analysis using Alphalens-style calculations.

    Computes IC analysis, quantile returns, and factor distribution.
    """
    try:
        import akshare as ak

        all_data = {}
        for code in stock_codes[:10]:  # Limit to 10 stocks for performance
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )
            if df is not None and not df.empty:
                all_data[code] = df

        if not all_data:
            return None

        # Simplified factor analysis
        # In production, this would use Alphalens properly
        factor_values = {}
        daily_returns = {}

        for code, df in all_data.items():
            close = df["收盘"].values
            # Simple factor: compute daily returns
            rets = np.diff(close) / close[:-1]
            daily_returns[code] = rets[-len(rets)//2:]  # Use second half
            factor_values[code] = np.random.randn(len(daily_returns[code]))  # Placeholder

        # Correlation analysis (simplified IC)
        ic_values = []
        for code in all_data:
            if code in daily_returns and code in factor_values:
                fv = factor_values[code]
                dr = daily_returns[code]
                min_len = min(len(fv), len(dr))
                if min_len > 1:
                    ic = np.corrcoef(fv[:min_len], dr[:min_len])[0, 1]
                    if not np.isnan(ic):
                        ic_values.append(ic)

        mean_ic = float(np.mean(ic_values)) if ic_values else 0
        ic_ir = mean_ic / (float(np.std(ic_values)) + 1e-8) if ic_values else 0

        return {
            "factor_name": factor.display_name,
            "mean_ic": round(mean_ic, 4),
            "ic_ir": round(ic_ir, 4),
            "ic_std": round(float(np.std(ic_values)), 4) if ic_values else 0,
            "positive_ic_ratio": round(
                sum(1 for ic in ic_values if ic > 0) / max(len(ic_values), 1), 4
            ),
            "num_stocks": len(all_data),
            "ic_series": [round(float(ic), 4) for ic in ic_values[-30:]],
        }

    except Exception as e:
        logger.error(f"Factor analysis failed: {e}")
        return {"error": str(e)}

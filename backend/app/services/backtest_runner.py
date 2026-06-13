"""Celery task to run backtest using Backtrader in a sandbox."""

import json
import logging
import traceback
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

import backtrader as bt
import pandas as pd

from app.core.celery_app import celery_app
from app.utils.sandbox import validate_strategy_code

logger = logging.getLogger(__name__)


class PandasData(bt.feeds.PandasData):
    """Backtrader data feed adapter for AKShare format."""
    params = (
        ('datetime', 'date'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
    )


@celery_app.task(
    name="app.services.backtest_runner.run_backtest",
    bind=True,
    max_retries=0,
    time_limit=300,  # 5 minutes hard limit
    soft_time_limit=240,
)
def run_backtest(self, task_id: str):
    """Execute a backtest task."""
    import asyncio
    from app.core.database import async_session
    from app.models.backtest_task import BacktestTask
    from sqlalchemy import select
    import akshare as ak

    async def _run():
        async with async_session() as db:
            # Load task
            stmt = select(BacktestTask).where(BacktestTask.id == UUID(task_id))
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                logger.error(f"Backtest task {task_id} not found")
                return

            try:
                task.status = "running"
                task.started_at = datetime.now(timezone.utc)
                await db.commit()

                # Validate strategy
                is_valid, errors = validate_strategy_code(task.strategy_code)
                if not is_valid:
                    task.status = "failed"
                    task.error_message = f"策略代码验证失败: {'; '.join(errors)}"
                    await db.commit()
                    return

                # Fetch historical data for each stock
                data_feeds = []
                for code in task.stock_codes:
                    df = ak.stock_zh_a_hist(
                        symbol=code,
                        period="daily",
                        start_date=task.start_date.strftime("%Y%m%d"),
                        end_date=task.end_date.strftime("%Y%m%d"),
                        adjust="qfq",
                    )
                    if df is None or df.empty:
                        continue

                    df['date'] = pd.to_datetime(df['日期'])
                    df.set_index('date', inplace=True)
                    df.rename(columns={
                        '开盘': 'open', '收盘': 'close', '最高': 'high',
                        '最低': 'low', '成交量': 'volume',
                    }, inplace=True)

                    data = PandasData(dataname=df)
                    data_feeds.append((code, data))

                if not data_feeds:
                    task.status = "failed"
                    task.error_message = "无法获取任何股票的历史数据"
                    await db.commit()
                    return

                # Setup Cerebro
                cerebro = bt.Cerebro()
                cerebro.broker.setcash(float(task.initial_capital))
                cerebro.broker.setcommission(commission=0.00025)

                for code, feed in data_feeds:
                    cerebro.adddata(feed, name=code)

                # Execute strategy code to get the strategy class
                strategy_globals = {
                    'bt': bt,
                    'pd': pd,
                    'np': __import__('numpy'),
                }
                strategy_locals = {}
                exec(task.strategy_code, strategy_globals, strategy_locals)

                # Find strategy class
                strategy_class = None
                for name, obj in strategy_locals.items():
                    if isinstance(obj, type) and issubclass(obj, bt.Strategy) and obj is not bt.Strategy:
                        strategy_class = obj
                        break

                if strategy_class is None:
                    task.status = "failed"
                    task.error_message = "策略代码中未找到Backtrader策略类"
                    await db.commit()
                    return

                cerebro.addstrategy(strategy_class)
                start_value = cerebro.broker.getvalue()
                results = cerebro.run()
                end_value = cerebro.broker.getvalue()

                # Extract metrics
                total_return = (end_value - start_value) / start_value
                equity_curve = []

                # Build equity curve from analyzers
                strat = results[0]
                try:
                    drawdown = strat.analyzers.getbyname('drawdown')
                    sharpe = strat.analyzers.getbyname('sharpe')
                    returns = strat.analyzers.getbyname('returns')

                    max_drawdown = drawdown.get_analysis().get('max', {}).get('drawdown', 0) if drawdown else 0
                    sharpe_ratio = sharpe.get_analysis().get('sharperatio', 0) if sharpe and sharpe.get_analysis().get('sharperatio') else 0
                except Exception:
                    max_drawdown = 0
                    sharpe_ratio = 0

                metrics = {
                    "total_return": round(total_return * 100, 2),
                    "annual_return": round(total_return * 100, 2),
                    "sharpe_ratio": round(float(sharpe_ratio) if sharpe_ratio else 0, 3),
                    "max_drawdown": round(float(max_drawdown) if max_drawdown else 0, 2),
                    "start_value": start_value,
                    "end_value": end_value,
                    "total_profit": end_value - start_value,
                }

                task.status = "completed"
                task.metrics = metrics
                task.result_data = {
                    "equity_curve": equity_curve,
                    "start_value": start_value,
                    "end_value": end_value,
                }
                task.completed_at = datetime.now(timezone.utc)
                await db.commit()

            except Exception as e:
                logger.error(f"Backtest failed for task {task_id}: {e}")
                task.status = "failed"
                task.error_message = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()[-500:]}"
                task.completed_at = datetime.now(timezone.utc)
                await db.commit()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()

    return {"task_id": task_id, "status": "completed"}

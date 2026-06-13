"""Backtest service — CRUD, task dispatching, results retrieval."""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.backtest_task import BacktestTask
from app.schemas.backtest import BacktestCreate
from app.utils.sandbox import validate_strategy_code

logger = logging.getLogger(__name__)


async def create_backtest_task(
    db: AsyncSession,
    user: User,
    data: BacktestCreate,
) -> BacktestTask:
    """Create a new backtest task and dispatch to Celery."""
    # Validate strategy code
    is_valid, errors = validate_strategy_code(data.strategy_code)
    if not is_valid:
        raise ValueError(f"策略代码验证失败: {'; '.join(errors)}")

    task = BacktestTask(
        user_id=user.id,
        name=data.name,
        strategy_code=data.strategy_code,
        stock_codes=data.stock_codes,
        start_date=data.start_date,
        end_date=data.end_date,
        initial_capital=data.initial_capital,
        parameters=data.parameters,
        status="pending",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Dispatch Celery task
    try:
        from app.core.celery_app import celery_app
        celery_result = celery_app.send_task(
            "app.services.backtest_runner.run_backtest",
            args=[str(task.id)],
        )
        task.celery_task_id = celery_result.id
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to dispatch backtest task: {e}")
        task.status = "failed"
        task.error_message = f"任务调度失败: {str(e)}"
        await db.commit()

    return task


async def get_user_tasks(
    db: AsyncSession,
    user: User,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[BacktestTask], int]:
    """Get paginated list of user's backtest tasks."""
    stmt = (
        select(BacktestTask)
        .where(BacktestTask.user_id == user.id)
        .order_by(BacktestTask.created_at.desc())
    )

    # Count total
    count_stmt = select(BacktestTask).where(BacktestTask.user_id == user.id)
    count_result = await db.execute(count_stmt)
    total = len(list(count_result.scalars().all()))

    # Paginate
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    tasks = list(result.scalars().all())

    return tasks, total


async def get_task(
    db: AsyncSession,
    user: User,
    task_id: UUID,
) -> Optional[BacktestTask]:
    """Get a single backtest task."""
    stmt = select(BacktestTask).where(
        BacktestTask.id == task_id,
        BacktestTask.user_id == user.id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_task_results(
    db: AsyncSession,
    user: User,
    task_id: UUID,
) -> Optional[dict]:
    """Get backtest task results including metrics and equity curve."""
    task = await get_task(db, user, task_id)
    if not task:
        return None

    return {
        "task_id": str(task.id),
        "status": task.status,
        "metrics": task.metrics,
        "result_data": task.result_data,
        "error_message": task.error_message,
    }

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.backtest import (
    BacktestCreate,
    BacktestResponse,
    BacktestResultResponse,
)
from app.services.backtest_service import (
    create_backtest_task,
    get_user_tasks,
    get_task,
    get_task_results,
)

router = APIRouter()


@router.post("/tasks", response_model=BacktestResponse, status_code=status.HTTP_201_CREATED)
async def create_backtest(
    data: BacktestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a new backtest task."""
    try:
        task = await create_backtest_task(db, current_user, data)
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/tasks", response_model=list[BacktestResponse])
async def list_backtests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's backtest tasks."""
    tasks, total = await get_user_tasks(db, current_user, page, page_size)
    return tasks


@router.get("/tasks/{task_id}", response_model=BacktestResponse)
async def get_backtest(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single backtest task."""
    task = await get_task(db, current_user, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


@router.get("/tasks/{task_id}/results", response_model=BacktestResultResponse)
async def get_backtest_results(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get backtest results (metrics + equity curve)."""
    result = await get_task_results(db, current_user, task_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return result

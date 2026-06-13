from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.watchlist_item import WatchlistItem
from app.schemas.dashboard import WatchlistCreate, WatchlistResponse, DashboardOverview
from app.services.dashboard_service import (
    get_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    get_dashboard_overview,
    get_account_summary,
)

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_overview(db, current_user)


@router.get("/account-summary")
async def account_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_account_summary(db, current_user)


@router.get("/watchlist", response_model=list[WatchlistResponse])
async def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await get_watchlist(db, current_user)
    return items


@router.post("/watchlist", response_model=WatchlistResponse)
async def add_watchlist(
    data: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await add_to_watchlist(db, current_user, data)


@router.delete("/watchlist/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await remove_from_watchlist(db, current_user, watchlist_id)
    return {"message": "已从自选股移除"}

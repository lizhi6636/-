from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.factor import (
    FactorCreate,
    FactorUpdate,
    FactorResponse,
    FactorPreviewRequest,
    FactorAnalysisRequest,
)
from app.services.factor_service import (
    get_all_factors,
    create_factor,
    update_factor,
    delete_factor,
    preview_factor_expression,
    analyze_factor,
)

router = APIRouter()


@router.get("/", response_model=list[FactorResponse])
async def list_factors(
    category: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_optional_user),
):
    """List all visible factors."""
    return await get_all_factors(db, current_user, category)


@router.post("/", response_model=FactorResponse, status_code=status.HTTP_201_CREATED)
async def create_factor_endpoint(
    data: FactorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom factor."""
    try:
        return await create_factor(db, current_user, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{factor_id}", response_model=FactorResponse)
async def update_factor_endpoint(
    factor_id: UUID,
    data: FactorUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a custom factor."""
    factor = await update_factor(db, current_user, factor_id, data)
    if not factor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在")
    return factor


@router.delete("/{factor_id}")
async def delete_factor_endpoint(
    factor_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom factor."""
    deleted = await delete_factor(db, current_user, factor_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在或无法删除")
    return {"message": "因子已删除"}


@router.post("/preview")
async def preview_factor(
    data: FactorPreviewRequest,
):
    """Preview factor expression on historical data."""
    result = await preview_factor_expression(
        data.expression,
        data.stock_code,
        data.start_date,
        data.end_date,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="因子计算失败")
    return result


@router.post("/analysis")
async def factor_analysis(
    data: FactorAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run factor analysis."""
    from sqlalchemy import select
    from app.models.factor_definition import FactorDefinition

    stmt = select(FactorDefinition).where(FactorDefinition.id == data.factor_id)
    result = await db.execute(stmt)
    factor = result.scalar_one_or_none()

    if not factor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在")

    analysis = await analyze_factor(
        factor,
        data.stock_codes,
        data.start_date,
        data.end_date,
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="因子分析失败")
    return analysis

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.learn_article import LearnArticle
from app.schemas.dashboard import LearnArticleResponse, LearnArticleDetail

router = APIRouter()


@router.get("/articles", response_model=list[LearnArticleResponse])
async def list_articles(
    category: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List published learning articles."""
    stmt = select(LearnArticle).where(LearnArticle.is_published == True)
    if category:
        stmt = stmt.where(LearnArticle.category == category)
    stmt = stmt.order_by(LearnArticle.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/articles/{article_id}", response_model=LearnArticleDetail)
async def get_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get article detail."""
    stmt = select(LearnArticle).where(LearnArticle.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    if not article:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    # Increment view count
    article.view_count += 1
    await db.commit()
    return article


@router.get("/cases", response_model=list[LearnArticleResponse])
async def list_cases(
    db: AsyncSession = Depends(get_db),
):
    """List strategy cases."""
    stmt = (
        select(LearnArticle)
        .where(LearnArticle.category == "case", LearnArticle.is_published == True)
        .order_by(LearnArticle.created_at.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

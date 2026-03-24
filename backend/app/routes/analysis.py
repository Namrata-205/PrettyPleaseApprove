from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.repositories.analysis_repository import AnalysisRepository
from app.models.analysis import AnalysisResult

router = APIRouter()


@router.get("/{pr_id}", response_model=AnalysisResult)
async def get_analysis(pr_id: int, db: AsyncSession = Depends(get_db)):
    repo = AnalysisRepository(db)
    result = await repo.get_by_pr_id(pr_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("", response_model=list[AnalysisResult])
async def list_analyses(db: AsyncSession = Depends(get_db)):
    repo = AnalysisRepository(db)
    return await repo.get_all()

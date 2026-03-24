from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, Boolean, DateTime, JSON, select
from sqlalchemy.sql import func
from app.database.connection import Base
from typing import Any


class AnalysisDB(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    pr_id = Column(Integer, nullable=False)
    repo_id = Column(Integer, nullable=False)
    ai_review = Column(JSON, nullable=False)
    sonar_result = Column(JSON, nullable=False)
    trivy_result = Column(JSON, nullable=False)
    passed = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(
        self,
        pr_id: int,
        repo_id: int,
        ai_review: dict[str, Any],
        sonar_result: dict[str, Any],
        trivy_result: dict[str, Any],
        passed: bool
    ) -> AnalysisDB:
        analysis = AnalysisDB(
            pr_id=pr_id,
            repo_id=repo_id,
            ai_review=ai_review,
            sonar_result=sonar_result,
            trivy_result=trivy_result,
            passed=passed
        )
        self.db.add(analysis)
        await self.db.flush()
        await self.db.refresh(analysis)
        return analysis

    async def get_by_pr_id(self, pr_id: int) -> AnalysisDB | None:
        result = await self.db.execute(
            select(AnalysisDB).where(AnalysisDB.pr_id == pr_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[AnalysisDB]:
        result = await self.db.execute(
            select(AnalysisDB).order_by(AnalysisDB.created_at.desc())
        )
        return list(result.scalars().all())

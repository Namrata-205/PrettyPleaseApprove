from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.repositories.repo_repository import RepoRepository
from app.models.repo import RepoRegisterRequest, RepoResponse

router = APIRouter()


@router.post("", response_model=RepoResponse)
async def register_repo(payload: RepoRegisterRequest, db: AsyncSession = Depends(get_db)):
    repo_repo = RepoRepository(db)
    existing = await repo_repo.get_by_name(payload.name)
    if existing:
        raise HTTPException(status_code=409, detail="Repo already registered")
    repo = await repo_repo.create(payload.name, payload.webhook_secret)
    return repo


@router.get("", response_model=list[RepoResponse])
async def list_repos(db: AsyncSession = Depends(get_db)):
    repo_repo = RepoRepository(db)
    return await repo_repo.get_all()

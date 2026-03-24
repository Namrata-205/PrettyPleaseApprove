from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, select
from app.database.connection import Base


class RepoDB(Base):
    __tablename__ = "repos"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    webhook_secret = Column(String, nullable=False)


class RepoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, webhook_secret: str) -> RepoDB:
        repo = RepoDB(name=name, webhook_secret=webhook_secret)
        self.db.add(repo)
        await self.db.flush()
        await self.db.refresh(repo)
        return repo

    async def get_by_name(self, name: str) -> RepoDB | None:
        result = await self.db.execute(
            select(RepoDB).where(RepoDB.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[RepoDB]:
        result = await self.db.execute(select(RepoDB))
        return list(result.scalars().all())

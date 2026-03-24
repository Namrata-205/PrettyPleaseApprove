from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import settings
from app.database.connection import init_db
from app.routes import webhook, repos, analysis, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="prettypleaseapprove",
    description="Automated PR reviewer bot",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
app.include_router(repos.router, prefix="/repos", tags=["repos"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}

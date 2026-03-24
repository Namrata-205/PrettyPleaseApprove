from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    app_port: int = 8000

    # GitHub
    github_token: str = ""
    github_webhook_secret: str = ""

    # Groq
    groq_api_key: str = ""

    # Jenkins
    jenkins_url: str = ""
    jenkins_user: str = ""
    jenkins_token: str = ""
    jenkins_job_name: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./local.db"

    # ✅ NEW STYLE (replaces class Config)
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
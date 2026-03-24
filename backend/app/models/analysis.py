from pydantic import BaseModel, ConfigDict
from typing import Any
from datetime import datetime


class AnalysisResult(BaseModel):
    id: int
    pr_id: int
    repo_id: int
    ai_review: dict[str, Any]
    sonar_result: dict[str, Any]
    trivy_result: dict[str, Any]
    passed: bool
    created_at: datetime

    # ✅ New style
    model_config = ConfigDict(from_attributes=True)
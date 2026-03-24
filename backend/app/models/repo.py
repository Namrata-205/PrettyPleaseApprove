from pydantic import BaseModel, ConfigDict


class RepoRegisterRequest(BaseModel):
    name: str
    webhook_secret: str


class RepoResponse(BaseModel):
    id: int
    name: str

    # ✅ New style
    model_config = ConfigDict(from_attributes=True)
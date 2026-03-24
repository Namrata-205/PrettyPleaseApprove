import httpx
from fastapi import APIRouter
from app.models.auth import TokenVerifyRequest, TokenVerifyResponse
from app.config import settings

router = APIRouter()


@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_token(payload: TokenVerifyRequest):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {payload.token}"}
        )
        if response.status_code == 200:
            data = response.json()
            return TokenVerifyResponse(valid=True, username=data.get("login"))
        return TokenVerifyResponse(valid=False)

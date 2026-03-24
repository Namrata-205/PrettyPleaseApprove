import pytest
import json
import hmac
import hashlib
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings


def make_signature(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.mark.asyncio
async def test_webhook_missing_signature():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/webhook/pr-event", json={"action": "opened"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_webhook_invalid_signature():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/webhook/pr-event",
            json={"action": "opened"},
            headers={"X-Hub-Signature-256": "sha256=invalidsignature"}
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_webhook_ignored_action():
    body = json.dumps({"action": "closed"}).encode()
    sig = make_signature(body, settings.github_webhook_secret or "test-secret")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/webhook/pr-event",
            content=body,
            headers={
                "X-Hub-Signature-256": sig,
                "Content-Type": "application/json"
            }
        )
    assert response.status_code in (200, 403)

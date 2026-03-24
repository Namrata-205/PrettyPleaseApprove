import hmac
import hashlib
from fastapi import Request, HTTPException
from app.config import settings


async def verify_github_signature(request: Request):
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing signature header")

    body = await request.body()

    expected = hmac.new(
        settings.github_webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    expected_header = f"sha256={expected}"

    if not hmac.compare_digest(expected_header, signature_header):
        raise HTTPException(status_code=403, detail="Invalid signature")

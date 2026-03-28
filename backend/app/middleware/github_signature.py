import hmac
import hashlib
from fastapi import Request, HTTPException
from app.config import settings


async def verify_github_signature(request: Request):
    """
    Validates X-Hub-Signature-256 header on incoming GitHub webhook payloads.
    Uses HMAC-SHA256 with the GITHUB_WEBHOOK_SECRET env var.
    Raises HTTP 403 if missing or invalid.
    """
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing X-Hub-Signature-256 header")

    body = await request.body()

    # hmac.new does not exist — correct API is hmac.new(key, msg, digestmod)
    # which is actually the HMAC constructor. Use hmac.new correctly:
    mac = hmac.new(
        settings.github_webhook_secret.encode("utf-8"),
        body,
        hashlib.sha256
    )
    expected_header = f"sha256={mac.hexdigest()}"

    if not hmac.compare_digest(expected_header, signature_header):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

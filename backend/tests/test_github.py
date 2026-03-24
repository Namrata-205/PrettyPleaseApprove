import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_fetch_pr_diff():
    mock_response = MagicMock()
    mock_response.text = "diff --git a/main.py b/main.py\n+print('hello')"
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.github.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.get = AsyncMock(return_value=mock_response)
        from app.services.github import fetch_pr_diff
        result = await fetch_pr_diff("org/repo", 1)

    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_post_pr_comment():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.github.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.post = AsyncMock(return_value=mock_response)
        from app.services.github import post_pr_comment
        await post_pr_comment("org/repo", 1, "## Review\nLooks good!")

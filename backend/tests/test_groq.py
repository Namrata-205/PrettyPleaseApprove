import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_review_diff_returns_issues():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = '{"issues": ["SQL injection risk on line 5"]}'

    with patch("app.services.ai_reviewer.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        from app.services.ai_reviewer import review_diff
        result = await review_diff("+ raw_query = f'SELECT * FROM users WHERE id={user_id}'")

    assert "issues" in result
    assert isinstance(result["issues"], list)


@pytest.mark.asyncio
async def test_review_diff_no_issues():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = '{"issues": []}'

    with patch("app.services.ai_reviewer.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        from app.services.ai_reviewer import review_diff
        result = await review_diff("+ x = 1 + 1")

    assert result["issues"] == []

import pytest
from app.services.jenkins import trigger_job, poll_result


@pytest.mark.asyncio
async def test_trigger_job_mock():
    # No jenkins_url set → returns mock job id
    result = await trigger_job(pr_id=42, repo="org/repo", branch="feature/test")
    assert result == "mock-job-123"


@pytest.mark.asyncio
async def test_poll_result_mock():
    result = await poll_result("mock-job-123")
    assert "sonar" in result
    assert "trivy" in result
    assert result["sonar"]["status"] == "passed"
    assert isinstance(result["trivy"]["vulnerabilities"], list)

import httpx
import asyncio
from app.config import settings
from typing import Any

AUTH = (settings.jenkins_user, settings.jenkins_token)


async def trigger_job(pr_id: int, repo: str, branch: str) -> str:
    if not settings.jenkins_url:
        return "mock-job-123"

    url = f"{settings.jenkins_url}/job/{settings.jenkins_job_name}/buildWithParameters"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            auth=AUTH,
            params={"PR_ID": pr_id, "REPO": repo, "BRANCH": branch}
        )
        response.raise_for_status()
        return response.headers.get("Location", "triggered")


async def poll_result(job_id: str, timeout: int = 120) -> dict[str, Any]:
    if not settings.jenkins_url or job_id == "mock-job-123":
        return {
            "sonar": {"status": "passed", "code_smells": 0, "coverage": 85},
            "trivy": {"vulnerabilities": []}
        }

    elapsed = 0
    interval = 5

    async with httpx.AsyncClient() as client:
        while elapsed < timeout:
            await asyncio.sleep(interval)
            elapsed += interval

            response = await client.get(
                f"{settings.jenkins_url}/job/{settings.jenkins_job_name}/lastBuild/api/json",
                auth=AUTH
            )
            data = response.json()

            if data.get("result") in ("SUCCESS", "FAILURE", "UNSTABLE"):
                return {
                    "sonar": data.get("sonar", {"status": "unknown", "code_smells": 0, "coverage": 0}),
                    "trivy": data.get("trivy", {"vulnerabilities": []})
                }

    return {
        "sonar": {"status": "timeout", "code_smells": 0, "coverage": 0},
        "trivy": {"vulnerabilities": []}
    }

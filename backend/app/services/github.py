import httpx
from app.config import settings

HEADERS = {
    "Authorization": f"Bearer {settings.github_token}",
    "Accept": "application/vnd.github.v3+json"
}


async def fetch_pr_diff(repo: str, pr_number: int) -> str:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={**HEADERS, "Accept": "application/vnd.github.v3.diff"}
        )
        response.raise_for_status()
        return response.text


async def post_pr_comment(repo: str, pr_number: int, comment: str) -> None:
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=HEADERS, json={"body": comment})
        response.raise_for_status()


async def set_pr_status(repo: str, sha: str, state: str, description: str) -> None:
    url = f"https://api.github.com/repos/{repo}/statuses/{sha}"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=HEADERS,
            json={
                "state": state,
                "description": description,
                "context": "prettypleaseapprove"
            }
        )
        response.raise_for_status()

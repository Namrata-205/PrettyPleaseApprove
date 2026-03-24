import asyncio
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.middleware.github_signature import verify_github_signature
from app.database.connection import get_db
from app.database.repositories.repo_repository import RepoRepository
from app.database.repositories.analysis_repository import AnalysisRepository
from app.services import github, jenkins, ai_reviewer, scorer
from app.utils.diff_parser import parse_diff
from app.utils.comment_formatter import format_comment

router = APIRouter()


@router.post("/pr-event")
async def handle_pr_event(request: Request, db: AsyncSession = Depends(get_db)):
    await verify_github_signature(request)

    payload = await request.json()
    action = payload.get("action")

    if action not in ("opened", "synchronize"):
        return JSONResponse({"message": "ignored"}, status_code=200)

    repo_name = payload["repository"]["full_name"]
    pr_number = payload["pull_request"]["number"]
    branch = payload["pull_request"]["head"]["ref"]
    sha = payload["pull_request"]["head"]["sha"]
    pr_id = payload["pull_request"]["id"]

    repo_repo = RepoRepository(db)
    repo = await repo_repo.get_by_name(repo_name)
    if not repo:
        return JSONResponse({"message": "repo not registered"}, status_code=404)

    # Fetch diff and trigger Jenkins in parallel
    diff_raw, job_id = await asyncio.gather(
        github.fetch_pr_diff(repo_name, pr_number),
        jenkins.trigger_job(pr_id, repo_name, branch)
    )

    parsed = parse_diff(diff_raw)

    # AI review and Jenkins poll in parallel
    ai_result, jenkins_result = await asyncio.gather(
        ai_reviewer.review_diff(parsed["raw"]),
        jenkins.poll_result(job_id)
    )

    sonar_result = jenkins_result.get("sonar", {})
    trivy_result = jenkins_result.get("trivy", {})

    score_result = scorer.score(ai_result, sonar_result, trivy_result)
    passed = scorer.is_passing(score_result)

    comment = format_comment(ai_result, sonar_result, trivy_result, passed)
    state = "success" if passed else "failure"
    description = "All checks passed" if passed else "Some checks failed — see review comment"

    await asyncio.gather(
        github.post_pr_comment(repo_name, pr_number, comment),
        github.set_pr_status(repo_name, sha, state, description)
    )

    analysis_repo = AnalysisRepository(db)
    await analysis_repo.save(pr_id, repo.id, ai_result, sonar_result, trivy_result, passed)

    return JSONResponse({"message": "review complete", "passed": passed})


@router.post("/jenkins-callback")
async def jenkins_callback(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    return JSONResponse({"message": "received", "payload": payload})

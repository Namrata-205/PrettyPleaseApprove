import json
import hmac
import hashlib
import asyncio
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.middleware.github_signature import verify_github_signature
from app.database.connection import get_db
from app.database.repositories.repo_repository import RepoRepository
from app.database.repositories.analysis_repository import AnalysisRepository
from app.services import github, ai_reviewer, scorer
from app.utils.diff_parser import parse_diff
from app.utils.comment_formatter import format_comment
from app.config import settings

router = APIRouter()


def _verify_bot_secret(request: Request):
    """Verify X-Bot-Secret header sent by Jenkins matches our configured secret."""
    if not settings.bot_secret:
        # Secret not configured — skip auth (dev mode only)
        return
    incoming = request.headers.get("X-Bot-Secret", "")
    expected = settings.bot_secret
    if not hmac.compare_digest(incoming, expected):
        raise HTTPException(status_code=403, detail="Invalid bot secret")


def _parse_sonar_result(raw: str | dict) -> dict:
    """
    Normalise SonarQube API response into the flat shape scorer.py expects.
    Jenkins sends the raw /api/qualitygates/project_status response:
      {"projectStatus": {"status": "OK", "conditions": [...]}}
    We flatten it to:
      {"status": "passed"|"failed"|"unknown", "coverage": float, "code_smells": int}
    """
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {"status": "unknown", "coverage": 0, "code_smells": 0}

    project_status = raw.get("projectStatus", {})
    gate_status = project_status.get("status", "UNKNOWN").upper()

    # Map SonarQube gate statuses → our internal status
    status = "passed" if gate_status == "OK" else ("failed" if gate_status == "ERROR" else "unknown")

    # Extract coverage and code_smells from conditions array if present
    coverage = 0.0
    code_smells = 0
    for condition in project_status.get("conditions", []):
        metric = condition.get("metricKey", "")
        value = condition.get("actualValue", "0")
        try:
            if metric == "coverage":
                coverage = float(value)
            elif metric in ("code_smells", "new_code_smells"):
                code_smells = int(float(value))
        except (ValueError, TypeError):
            pass

    return {"status": status, "coverage": coverage, "code_smells": code_smells}


def _parse_trivy_report(raw: str | dict | list) -> dict:
    """
    Normalise Trivy JSON output into the flat shape scorer.py expects.
    Trivy outputs:
      {"Results": [{"Vulnerabilities": [{"VulnerabilityID": "...", "Severity": "HIGH", ...}]}]}
    We flatten to:
      {"vulnerabilities": [{"severity": "HIGH", "id": "CVE-...", "pkg": "..."}]}
    """
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {"vulnerabilities": []}

    # Trivy can return a list or a dict with "Results" key
    results = []
    if isinstance(raw, list):
        results = raw
    elif isinstance(raw, dict):
        results = raw.get("Results", [])

    vulns = []
    for result in results:
        for v in (result.get("Vulnerabilities") or []):
            vulns.append({
                "severity": v.get("Severity", "UNKNOWN").upper(),
                "id": v.get("VulnerabilityID", ""),
                "pkg": v.get("PkgName", ""),
                "title": v.get("Title", ""),
                "fixed_version": v.get("FixedVersion", ""),
            })

    return {"vulnerabilities": vulns}


@router.post("/pr-event")
async def handle_pr_event(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handles GitHub webhook PR events (opened / synchronize).
    This is the PUSH flow: GitHub → bot → Jenkins trigger → poll → comment.
    """
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

    # Fetch diff — Jenkins will be triggered by the webhook separately
    diff_raw = await github.fetch_pr_diff(repo_name, pr_number)
    parsed = parse_diff(diff_raw)

    # AI review the diff immediately (Jenkins results come via callback)
    ai_result = await ai_reviewer.review_diff(parsed["raw"])

    # Store partial result; Jenkins callback will complete it
    analysis_repo = AnalysisRepository(db)
    await analysis_repo.save(
        pr_id, repo.id, ai_result,
        sonar_result={}, trivy_result={}, passed=False
    )

    return JSONResponse({"message": "ai_review_queued", "pr_id": pr_id})


@router.post("/jenkins-callback")
async def jenkins_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Called by Jenkins after SonarQube + Trivy stages complete.
    Payload from Jenkinsfile:
      {
        "pr_number": 42,
        "repo": "owner/repo",
        "head_sha": "abc123",
        "branch": "feature/foo",
        "target_branch": "main",
        "jenkins_build": "http://jenkins/job/...",
        "sonar_result": "<raw SonarQube API JSON string>",
        "trivy_report": "<raw Trivy JSON string>"
      }
    """
    _verify_bot_secret(request)

    payload = await request.json()

    repo_name = payload.get("repo", "")
    pr_number = payload.get("pr_number")
    head_sha = payload.get("head_sha", "")
    jenkins_build = payload.get("jenkins_build", "")

    if not repo_name or not pr_number:
        raise HTTPException(status_code=400, detail="Missing repo or pr_number")

    # Normalise scan results from Jenkins into scorer-compatible shapes
    sonar_result = _parse_sonar_result(payload.get("sonar_result", "{}"))
    trivy_result = _parse_trivy_report(payload.get("trivy_report", "{}"))

    # Fetch the PR diff for AI review
    try:
        diff_raw = await github.fetch_pr_diff(repo_name, pr_number)
        parsed = parse_diff(diff_raw)
        ai_result = await ai_reviewer.review_diff(parsed["raw"])
    except Exception as e:
        # Don't fail the whole review if AI is unavailable
        ai_result = {"issues": [f"AI review unavailable: {str(e)}"]}

    # Score everything together
    score_result = scorer.score(ai_result, sonar_result, trivy_result)
    passed = scorer.is_passing(score_result)

    # Format and post the GitHub PR comment
    comment = format_comment(ai_result, sonar_result, trivy_result, passed)
    state = "success" if passed else "failure"
    description = "All checks passed" if passed else "Review found issues — see comment"

    await asyncio.gather(
        github.post_pr_comment(repo_name, pr_number, comment),
        github.set_pr_status(repo_name, head_sha, state, description),
    )

    # Persist to DB
    repo_repo = RepoRepository(db)
    repo = await repo_repo.get_by_name(repo_name)
    if repo:
        analysis_repo = AnalysisRepository(db)
        await analysis_repo.save(
            pr_number, repo.id, ai_result, sonar_result, trivy_result, passed
        )

    return JSONResponse({
        "message": "review complete",
        "passed": passed,
        "score_breakdown": score_result.get("breakdown", {}),
        "issues_found": len(score_result.get("issues", [])),
    })

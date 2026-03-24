from typing import Any

COVERAGE_THRESHOLD = 80
MAX_CODE_SMELLS = 5
MAX_HIGH_VULNS = 0
MAX_MEDIUM_VULNS = 3


def score(
    ai_review: dict[str, Any],
    sonar_result: dict[str, Any],
    trivy_result: dict[str, Any]
) -> dict[str, Any]:
    issues = []

    # AI review check
    ai_issues = ai_review.get("issues", [])
    ai_passed = len(ai_issues) == 0

    # Sonar checks
    coverage = sonar_result.get("coverage", 0)
    code_smells = sonar_result.get("code_smells", 0)
    sonar_status = sonar_result.get("status", "unknown")
    sonar_passed = (
        coverage >= COVERAGE_THRESHOLD
        and code_smells <= MAX_CODE_SMELLS
        and sonar_status == "passed"
    )
    if coverage < COVERAGE_THRESHOLD:
        issues.append(f"Coverage {coverage}% is below threshold of {COVERAGE_THRESHOLD}%")
    if code_smells > MAX_CODE_SMELLS:
        issues.append(f"{code_smells} code smells found (max {MAX_CODE_SMELLS} allowed)")

    # Trivy checks
    vulns = trivy_result.get("vulnerabilities", [])
    high_vulns = [v for v in vulns if v.get("severity") in ("HIGH", "CRITICAL")]
    medium_vulns = [v for v in vulns if v.get("severity") == "MEDIUM"]
    trivy_passed = len(high_vulns) <= MAX_HIGH_VULNS and len(medium_vulns) <= MAX_MEDIUM_VULNS

    if high_vulns:
        issues.append(f"{len(high_vulns)} HIGH/CRITICAL vulnerabilities found")
    if len(medium_vulns) > MAX_MEDIUM_VULNS:
        issues.append(f"{len(medium_vulns)} MEDIUM vulnerabilities found (max {MAX_MEDIUM_VULNS})")

    passed = ai_passed and sonar_passed and trivy_passed

    return {
        "passed": passed,
        "issues": issues,
        "breakdown": {
            "ai_passed": ai_passed,
            "sonar_passed": sonar_passed,
            "trivy_passed": trivy_passed
        }
    }


def is_passing(score_result: dict[str, Any]) -> bool:
    return score_result.get("passed", False)

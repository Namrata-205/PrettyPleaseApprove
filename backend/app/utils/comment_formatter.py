from typing import Any


def format_comment(
    ai_review: dict[str, Any],
    sonar_result: dict[str, Any],
    trivy_result: dict[str, Any],
    passed: bool
) -> str:
    verdict = "✅ APPROVED — ready to merge" if passed else "❌ BLOCKED — fix issues before merging"

    ai_issues = ai_review.get("issues", [])
    ai_section = "\n".join(f"- {issue}" for issue in ai_issues) or "No issues found."

    sonar_smells = sonar_result.get("code_smells", 0)
    sonar_coverage = sonar_result.get("coverage", 0)
    sonar_status = sonar_result.get("status", "unknown")

    trivy_vulns = trivy_result.get("vulnerabilities", [])
    trivy_section = "\n".join(
        f"- [{v.get('severity')}] {v.get('id')} in {v.get('package')}"
        for v in trivy_vulns
    ) or "No vulnerabilities found."

    return f"""## 🤖 prettypleaseapprove review

### Verdict: {verdict}

---

### 🧠 AI Review (Groq)
{ai_section}

---

### 📊 SonarQube
- Status: `{sonar_status}`
- Code smells: `{sonar_smells}`
- Coverage: `{sonar_coverage}%`

---

### 🔒 Trivy Security Scan
{trivy_section}

---
*Reviewed automatically. Push a fix to re-trigger the review.*
"""

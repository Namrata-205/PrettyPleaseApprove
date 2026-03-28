from typing import Any


def format_comment(
    ai_result: dict[str, Any],
    sonar_result: dict[str, Any],
    trivy_result: dict[str, Any],
    passed: bool,
) -> str:
    """
    Formats the full PR review comment posted to GitHub.
    All inputs use the normalised internal shapes (after parsing in webhook.py).
    """
    lines = []

    # ── Header ───────────────────────────────────────────────────────
    verdict = "✅ Approved" if passed else "⚠️ Changes requested"
    lines.append(f"## 🤖 PrettyPleaseApprove — {verdict}")
    lines.append("")

    # ── Score table ──────────────────────────────────────────────────
    ai_issues = ai_result.get("issues", [])
    ai_icon = "✅" if not ai_issues else "⚠️"

    sonar_status = sonar_result.get("status", "unknown")
    sonar_icon = "✅" if sonar_status == "passed" else ("❌" if sonar_status == "failed" else "⚪")

    vulns = trivy_result.get("vulnerabilities", [])
    high = [v for v in vulns if v.get("severity") in ("HIGH", "CRITICAL")]
    medium = [v for v in vulns if v.get("severity") == "MEDIUM"]
    trivy_icon = "✅" if not high and len(medium) <= 3 else "⚠️"

    lines.append("| Check | Result |")
    lines.append("|---|---|")
    ai_summary = f"{len(ai_issues)} issue(s)" if ai_issues else "No issues"
    lines.append(f"| {ai_icon} AI Code Review | {ai_summary} |")
    sonar_label = sonar_status.upper()
    coverage = sonar_result.get("coverage", 0)
    smells = sonar_result.get("code_smells", 0)
    lines.append(f"| {sonar_icon} SonarQube | Gate: {sonar_label} · Coverage: {coverage:.0f}% · Smells: {smells} |")
    trivy_label = f"{len(high)} HIGH/CRITICAL, {len(medium)} MEDIUM" if vulns else "No vulnerabilities"
    lines.append(f"| {trivy_icon} Trivy Security | {trivy_label} |")
    lines.append("")

    # ── AI findings ──────────────────────────────────────────────────
    if ai_issues:
        lines.append("### 🔍 AI Review Findings")
        lines.append("")
        for issue in ai_issues:
            lines.append(f"- {issue}")
        lines.append("")

    # ── SonarQube detail ─────────────────────────────────────────────
    if sonar_status != "passed":
        lines.append("<details>")
        lines.append("<summary>SonarQube details</summary>")
        lines.append("")
        lines.append(f"- Gate status: **{sonar_label}**")
        lines.append(f"- Coverage: **{coverage:.1f}%** (threshold: 80%)")
        lines.append(f"- Code smells: **{smells}**")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    # ── Trivy findings ───────────────────────────────────────────────
    if vulns:
        lines.append("<details>")
        lines.append(f"<summary>Security scan — {len(vulns)} finding(s)</summary>")
        lines.append("")
        lines.append("| Severity | ID | Package | Fix available |")
        lines.append("|---|---|---|---|")
        # Show HIGH/CRITICAL first, then MEDIUM
        sorted_vulns = sorted(
            vulns,
            key=lambda v: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}.get(v.get("severity", "UNKNOWN"), 4)
        )
        for v in sorted_vulns[:20]:  # cap at 20 rows to avoid mega-comments
            fix = v.get("fixed_version") or "—"
            lines.append(f"| {v.get('severity','')} | {v.get('id','')} | {v.get('pkg','')} | {fix} |")
        if len(vulns) > 20:
            lines.append(f"| … | +{len(vulns) - 20} more | | |")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    # ── Footer ───────────────────────────────────────────────────────
    lines.append("---")
    lines.append("*Powered by [PrettyPleaseApprove](https://github.com/Namrata-205/PrettyPleaseApprove)*")

    return "\n".join(lines)

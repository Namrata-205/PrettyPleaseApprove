from app.services.scorer import score, is_passing


def test_all_passing():
    result = score(
        ai_review={"issues": []},
        sonar_result={"status": "passed", "coverage": 90, "code_smells": 2},
        trivy_result={"vulnerabilities": []}
    )
    assert result["passed"] is True
    assert is_passing(result) is True


def test_fails_low_coverage():
    result = score(
        ai_review={"issues": []},
        sonar_result={"status": "passed", "coverage": 50, "code_smells": 0},
        trivy_result={"vulnerabilities": []}
    )
    assert result["passed"] is False
    assert any("Coverage" in i for i in result["issues"])


def test_fails_high_vulnerability():
    result = score(
        ai_review={"issues": []},
        sonar_result={"status": "passed", "coverage": 90, "code_smells": 0},
        trivy_result={"vulnerabilities": [{"severity": "HIGH", "id": "CVE-2024-1234", "package": "requests"}]}
    )
    assert result["passed"] is False


def test_fails_ai_issues():
    result = score(
        ai_review={"issues": ["SQL injection risk"]},
        sonar_result={"status": "passed", "coverage": 90, "code_smells": 0},
        trivy_result={"vulnerabilities": []}
    )
    assert result["passed"] is False

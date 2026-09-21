import json
import subprocess
import tempfile
from pathlib import Path

from app.schemas.review import (
    IssueCategory,
    ReviewIssue,
    Severity,
)


def run_static_analysis(code: str, language: str) -> list[ReviewIssue]:
    if language.lower() != "python":
        return []

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "reviewed_code.py"
        file_path.write_text(code, encoding="utf-8")

        issues = []

        issues.extend(run_ruff(file_path))
        issues.extend(run_bandit(file_path))

        return issues


def run_ruff(file_path: Path) -> list[ReviewIssue]:
    result = subprocess.run(
        [
            "ruff",
            "check",
            str(file_path),
            "--output-format",
            "json",
        ],
        capture_output=True,
        text=True,
    )

    if not result.stdout:
        return []

    try:
        findings = json.loads(result.stdout)

        
    except json.JSONDecodeError:
        return []

    issues = []

    for finding in findings:
        severity = map_ruff_severity(finding["code"])

        issues.append(
            ReviewIssue(
                category=IssueCategory.CODE_QUALITY,
                severity=severity,
                file=None,
                line_start=finding["location"]["row"],
                line_end=finding["end_location"]["row"],
                title=finding["message"],
                description=(
                    f"Ruff rule {finding['code']} detected this issue."
                ),
                suggestion=(
                    "Review the reported issue and apply the recommended "
                    "code-quality improvement."
                ),
                confidence=1.0,
                source="ruff",
                rule_id=finding["code"],
            )
        )

    return issues

def get_bandit_suggestion(finding: dict) -> str:
    suggestions = {
        "B105": (
            "Remove the hard-coded credential. "
            "Load secrets from environment variables or a "
            "dedicated secret manager."
        ),
        "B307": (
            "Avoid eval(). Use a safe parser such as "
            "ast.literal_eval() when appropriate, or explicitly "
            "validate and whitelist allowed input."
        ),
        "B605": (
            "Avoid executing commands through a shell. "
            "Use subprocess.run() with shell=False and pass "
            "arguments as a list whenever possible."
        ),
        "B607": (
            "Avoid relying on partial executable paths. "
            "Use an explicit executable path or otherwise "
            "validate the executable being invoked."
        ),
    }

    test_id = finding.get("test_id")

    if test_id in suggestions:
        return suggestions[test_id]

    return (
        "Review the reported security issue and apply the "
        "recommended secure alternative."
    )


def run_bandit(file_path: Path) -> list[ReviewIssue]:
    result = subprocess.run(
        [
            "bandit",
            "-f",
            "json",
            "-q",
            str(file_path),
        ],
        capture_output=True,
        text=True,
    )

    if not result.stdout:
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    issues = []

    for finding in data.get("results", []):

        # Ignore generic import blacklist warnings when
        # Bandit has a more specific finding for the same code.
        if finding.get("test_id") == "B404":
            continue
        severity = map_bandit_severity(
            finding.get("issue_severity", "LOW")
        )

        issues.append(
            ReviewIssue(
                category=IssueCategory.SECURITY,
                severity=severity,
                file=None,
                line_start=finding.get("line_number"),
                line_end=finding.get("line_number"),
                title=finding["test_name"],
                description=finding["issue_text"],
                suggestion=(
                    get_bandit_suggestion(finding)
                    or "Review and remediate the security issue."
                ),
                confidence=map_bandit_confidence(
                    finding.get("issue_confidence", "MEDIUM")
                ),
                source="bandit",
                rule_id=finding.get("test_id"),
            )
        )

    return issues


def map_ruff_severity(rule_code: str) -> Severity:
    if rule_code.startswith(("S",)):
        return Severity.HIGH

    return Severity.LOW


def map_bandit_severity(value: str) -> Severity:
    value = value.upper()

    if value == "HIGH":
        return Severity.HIGH

    if value == "MEDIUM":
        return Severity.MEDIUM

    return Severity.LOW


def map_bandit_confidence(value: str) -> float:
    value = value.upper()

    if value == "HIGH":
        return 0.95

    if value == "MEDIUM":
        return 0.80

    return 0.60
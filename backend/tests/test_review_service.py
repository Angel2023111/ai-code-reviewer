from app.schemas.review import (
    IssueCategory,
    ReviewIssue,
    Severity,
)
from app.services.review_service import review_code


def make_llm_issue(
    category,
    severity,
    title,
    description,
    line_start,
    line_end,
):
    return ReviewIssue(
        category=category,
        severity=severity,
        file=None,
        line_start=line_start,
        line_end=line_end,
        title=title,
        description=description,
        suggestion="Fix the issue.",
        confidence=0.9,
        source="llm",
        rule_id=None,
    )


def test_review_pipeline_merges_static_and_llm_findings():
    def fake_llm(code, language):
        return [
            make_llm_issue(
                category=IssueCategory.SECURITY,
                severity=Severity.HIGH,
                title="Hardcoded password",
                description="A password is hardcoded.",
                line_start=3,
                line_end=3,
            )
        ]

    code = """
def login():
    password = "admin123"
    return password
"""

    response = review_code(
        code,
        "python",
        llm_reviewer=fake_llm,
    )

    assert response.review_id is not None

    assert len(response.issues) == 1

    issue = response.issues[0]

    assert issue.category == IssueCategory.SECURITY
    assert issue.source == "bandit"
    assert issue.rule_id == "B105"


def test_review_pipeline_detects_eval_issue_without_llm_findings():
    def fake_llm(code, language):
        return []

    code = """
def run(user_input):
    return eval(user_input)
"""

    response = review_code(
        code,
        "python",
        llm_reviewer=fake_llm,
    )

    assert len(response.issues) >= 1

    assert any(
        issue.category == IssueCategory.SECURITY
        and "eval" in (
            issue.title + " " + issue.description
        ).lower()
        for issue in response.issues
    )


def test_review_summary_matches_final_issues():
    def fake_llm(code, language):
        return []

    code = """
def run(user_input):
    return eval(user_input)
"""

    response = review_code(
        code,
        "python",
        llm_reviewer=fake_llm,
    )

    total = (
        response.summary.critical
        + response.summary.high
        + response.summary.medium
        + response.summary.low
    )

    assert total == len(response.issues)


def test_review_pipeline_handles_clean_code():
    def fake_llm(code, language):
        return []

    code = """
def add(a, b):
    return a + b
"""

    response = review_code(
        code,
        "python",
        llm_reviewer=fake_llm,
    )

    assert response.issues == []

    assert response.summary.critical == 0
    assert response.summary.high == 0
    assert response.summary.medium == 0
    assert response.summary.low == 0
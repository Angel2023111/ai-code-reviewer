from app.schemas.review import (
    IssueCategory,
    ReviewIssue,
    Severity,
)

from app.services.pr_classification_service import (
    FindingStatus,
    classify_finding,
)


def make_issue(
    line_start: int | None,
    line_end: int | None = None,
) -> ReviewIssue:
    return ReviewIssue(
        category=IssueCategory.SECURITY,
        severity=Severity.HIGH,
        file="app.py",
        line_start=line_start,
        line_end=line_end,
        title="Security issue",
        description="Test security issue",
        suggestion="Fix the issue",
        confidence=0.95,
        source="ast",
        rule_id="test-rule",
    )


def test_finding_on_changed_line_is_introduced():
    issue = make_issue(12)

    result = classify_finding(
        issue,
        changed_lines=[12, 15],
    )

    assert result == FindingStatus.INTRODUCED


def test_finding_outside_changed_lines_is_pre_existing():
    issue = make_issue(5)

    result = classify_finding(
        issue,
        changed_lines=[12, 15],
    )

    assert result == FindingStatus.PRE_EXISTING


def test_multiline_finding_overlapping_change_is_introduced():
    issue = make_issue(10, 14)

    result = classify_finding(
        issue,
        changed_lines=[12],
    )

    assert result == FindingStatus.INTRODUCED


def test_finding_without_line_is_pre_existing():
    issue = make_issue(None)

    result = classify_finding(
        issue,
        changed_lines=[12],
    )

    assert result == FindingStatus.PRE_EXISTING
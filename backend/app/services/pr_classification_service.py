from app.schemas.review import (
    FindingStatus,
    ReviewIssue,
)


def classify_finding(
    issue: ReviewIssue,
    changed_lines: list[int],
) -> FindingStatus:
    if issue.line_start is None:
        return FindingStatus.PRE_EXISTING

    if issue.line_end is None:
        issue_lines = [issue.line_start]
    else:
        issue_lines = range(
            issue.line_start,
            issue.line_end + 1,
        )

    changed_line_set = set(changed_lines)

    if any(
        line in changed_line_set
        for line in issue_lines
    ):
        return FindingStatus.INTRODUCED

    return FindingStatus.PRE_EXISTING
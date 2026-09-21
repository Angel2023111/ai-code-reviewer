import pytest

from app.services.github_service import GitHubAPIError

from unittest.mock import patch

from app.services.pr_review_service import (
    review_pr_file,
    review_pull_request,
)
from app.schemas.review import (
    FindingStatus,
    ReviewResponse,
    ReviewSummary,
)

from app.schemas.review import (
    FindingStatus,
    IssueCategory,
    ReviewIssue,
    ReviewResponse,
    ReviewSummary,
    Severity,
)


def test_review_pr_file():
    pr_file = {
        "filename": "app.py",
        "language": "python",
        "source_code": "print('hello')",
        "changed_lines": [2],
    }

    from app.schemas.review import (
        FindingStatus,
        IssueCategory,
        ReviewIssue,
        ReviewResponse,
        ReviewSummary,
        Severity,
    )

    fake_issue = ReviewIssue(
        category=IssueCategory.SECURITY,
        severity=Severity.HIGH,
        file=None,
        line_start=2,
        line_end=2,
        title="Use of eval",
        description="eval can execute arbitrary code.",
        suggestion="Avoid eval.",
        confidence=0.98,
        source="ast",
        rule_id="dangerous-call",
    )

    fake_response = ReviewResponse(
        review_id="test-review",
        summary=ReviewSummary(
            critical=0,
            high=1,
            medium=0,
            low=0,
        ),
        issues=[fake_issue],
    )

    with patch(
        "app.services.pr_review_service.review_code",
        return_value=fake_response,
    ) as mock_review:

        result = review_pr_file(pr_file)

    assert result == fake_response

    assert result.issues[0].pr_status == FindingStatus.INTRODUCED

    mock_review.assert_called_once_with(
        code="print('hello')",
        language="python",
    )

def test_review_pr_file_classifies_introduced_and_pre_existing_findings(
    monkeypatch,
):
    introduced_issue = ReviewIssue(
        category=IssueCategory.SECURITY,
        severity=Severity.HIGH,
        file=None,
        line_start=2,
        line_end=2,
        title="Use of eval",
        description="eval can execute arbitrary code.",
        suggestion="Avoid eval.",
        confidence=0.98,
        source="ast",
        rule_id="dangerous-call",
    )

    pre_existing_issue = ReviewIssue(
        category=IssueCategory.SECURITY,
        severity=Severity.HIGH,
        file=None,
        line_start=8,
        line_end=8,
        title="Use of eval",
        description="eval can execute arbitrary code.",
        suggestion="Avoid eval.",
        confidence=0.98,
        source="ast",
        rule_id="dangerous-call",
    )

    fake_response = ReviewResponse(
        review_id="test-review",
        summary=ReviewSummary(
            critical=0,
            high=2,
            medium=0,
            low=0,
        ),
        issues=[
            introduced_issue,
            pre_existing_issue,
        ],
    )

    def fake_review_code(code, language):
        return fake_response

    monkeypatch.setattr(
        "app.services.pr_review_service.review_code",
        fake_review_code,
    )

    pr_file = {
        "filename": "app.py",
        "language": "python",
        "source_code": "some code",
        "changed_lines": [2, 5],
    }

    result = review_pr_file(pr_file)

    assert result.issues[0].pr_status == FindingStatus.INTRODUCED
    assert result.issues[1].pr_status == FindingStatus.PRE_EXISTING

def test_review_pull_request():
    github_files = [
        {
            "filename": "app.py",
            "patch": """@@ -1,2 +1,3 @@
 def process(data):
+    result = eval(data)
     return result
""",
        },
        {
            "filename": "README.md",
            "patch": """@@ -1,2 +1,3 @@
 old
+new
""",
        },
    ]

    source_code = """def process(data):
    result = eval(data)
    return result
"""

    fake_response = ReviewResponse(
        review_id="test-review",
        summary=ReviewSummary(
            critical=1,
            high=0,
            medium=0,
            low=0,
        ),
        issues=[],
    )

    with (
        patch(
            "app.services.pr_review_service.get_pull_request_files",
            return_value=github_files,
        ) as mock_get_files,
        patch(
            "app.services.pr_review_service.get_file_contents",
            return_value=source_code,
        ) as mock_get_contents,
        patch(
            "app.services.pr_review_service.review_pr_file",
            return_value=fake_response,
        ) as mock_review,
    ):

        result = review_pull_request(
            owner="test-owner",
            repo="test-repo",
            pull_number=12,
            head_sha="abc123",
        )

    assert len(result) == 1

    assert result[0]["filename"] == "app.py"

    assert result[0]["changed_lines"] == [2]

    assert result[0]["review"] == fake_response

    mock_get_files.assert_called_once_with(
        owner="test-owner",
        repo="test-repo",
        pull_number=12,
    )

    mock_get_contents.assert_called_once_with(
        owner="test-owner",
        repo="test-repo",
        path="app.py",
        ref="abc123",
    )

    mock_review.assert_called_once()

def test_review_pull_request_propagates_github_api_error(
    monkeypatch,
):
    def fake_get_pull_request_files(
        owner,
        repo,
        pull_number,
    ):
        raise GitHubAPIError(
            "GitHub API request failed."
        )

    monkeypatch.setattr(
        "app.services.pr_review_service.get_pull_request_files",
        fake_get_pull_request_files,
    )

    with pytest.raises(GitHubAPIError):
        review_pull_request(
            owner="test-owner",
            repo="test-repo",
            pull_number=1,
            head_sha="abc123",
        )

def test_review_pull_request_handles_mixed_files():
    github_files = [
        {
            "filename": "app.py",
            "status": "modified",
            "patch": "@@ -1 +1 @@\n+print('app')",
        },
        {
            "filename": "utils.py",
            "status": "renamed",
            "previous_filename": "old_utils.py",
            "patch": "@@ -1 +1 @@\n+print('utils')",
        },
        {
            "filename": "README.md",
            "status": "modified",
            "patch": "@@ -1 +1 @@\n+new documentation",
        },
        {
            "filename": "image.png",
            "status": "modified",
            "patch": None,
        },
        {
            "filename": "deleted.py",
            "status": "removed",
            "patch": "@@ -1 +0 @@\n-old code",
        },
    ]

    source_codes = {
        "app.py": "print('app')",
        "utils.py": "print('utils')",
    }

    fake_response = ReviewResponse(
        review_id="test-review",
        summary=ReviewSummary(
            critical=0,
            high=0,
            medium=0,
            low=0,
        ),
        issues=[],
    )

    def fake_get_file_contents(
        owner,
        repo,
        path,
        ref,
    ):
        return source_codes[path]

    with (
        patch(
            "app.services.pr_review_service.get_pull_request_files",
            return_value=github_files,
        ),
        patch(
            "app.services.pr_review_service.get_file_contents",
            side_effect=fake_get_file_contents,
        ) as mock_get_contents,
        patch(
            "app.services.pr_review_service.review_pr_file",
            return_value=fake_response,
        ) as mock_review,
    ):
        result = review_pull_request(
            owner="test-owner",
            repo="test-repo",
            pull_number=12,
            head_sha="abc123",
        )

    assert len(result) == 2

    assert [item["filename"] for item in result] == [
        "app.py",
        "utils.py",
    ]

    assert mock_get_contents.call_count == 2
    assert mock_review.call_count == 2
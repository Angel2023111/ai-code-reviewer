import json

import pytest

from app.schemas.review import (
    IssueCategory,
    Severity,
)
from app.services.llm_service import parse_llm_response


def test_valid_llm_response_is_parsed():
    content = json.dumps({
        "issues": [
            {
                "category": "SECURITY",
                "severity": "HIGH",
                "file": None,
                "line_start": 5,
                "line_end": 5,
                "title": "Hardcoded password",
                "description": (
                    "A password is stored directly in source code."
                ),
                "suggestion": (
                    "Use an environment variable or secrets manager."
                ),
                "confidence": 0.95,
            }
        ]
    })

    issues = parse_llm_response(content)

    assert len(issues) == 1

    issue = issues[0]

    assert issue.category == IssueCategory.SECURITY
    assert issue.severity == Severity.HIGH
    assert issue.line_start == 5
    assert issue.source == "llm"


def test_empty_response_raises_error():
    with pytest.raises(RuntimeError, match="empty response"):
        parse_llm_response("")


def test_invalid_json_raises_error():
    with pytest.raises(RuntimeError, match="invalid JSON"):
        parse_llm_response("this is not json")


def test_invalid_schema_raises_error():
    content = json.dumps({
        "issues": [
            {
                "category": "NOT_A_REAL_CATEGORY",
                "severity": "HIGH",
                "file": None,
                "line_start": 5,
                "line_end": 5,
                "title": "Test",
                "description": "Test",
                "suggestion": "Test",
                "confidence": 0.9,
            }
        ]
    })

    with pytest.raises(
        RuntimeError,
        match="invalid review format",
    ):
        parse_llm_response(content)


def test_empty_issue_list_is_valid():
    content = json.dumps({
        "issues": []
    })

    issues = parse_llm_response(content)

    assert issues == []


def test_llm_source_is_added_to_every_issue():
    content = json.dumps({
        "issues": [
            {
                "category": "BUG",
                "severity": "MEDIUM",
                "file": "main.py",
                "line_start": 10,
                "line_end": 10,
                "title": "Possible runtime error",
                "description": "The operation may fail.",
                "suggestion": "Validate the input first.",
                "confidence": 0.8,
            },
            {
                "category": "CODE_QUALITY",
                "severity": "LOW",
                "file": "main.py",
                "line_start": 20,
                "line_end": 20,
                "title": "Duplicated logic",
                "description": "The same logic is repeated.",
                "suggestion": "Extract a helper function.",
                "confidence": 0.85,
            },
        ]
    })

    issues = parse_llm_response(content)

    assert len(issues) == 2

    assert all(
        issue.source == "llm"
        for issue in issues
    )
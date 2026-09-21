from uuid import uuid4
from typing import Callable

from app.schemas.review import (
    ReviewIssue,
    ReviewResponse,
    ReviewSummary,
    Severity,
)

from app.services.llm_service import review_with_llm
from app.services.static_analysis_service import run_static_analysis
from app.services.ast_analysis_service import run_ast_analysis
from app.services.aggregator_service import aggregate_issues


LLMReviewer = Callable[
    [str, str],
    list[ReviewIssue],
]


def review_code(
    code: str,
    language: str,
    llm_reviewer: LLMReviewer = review_with_llm,
) -> ReviewResponse:

    static_issues = run_static_analysis(
        code=code,
        language=language,
    )

    ast_issues = run_ast_analysis(
        code=code,
        language=language,
    )

    llm_issues = llm_reviewer(
        code,
        language,
    )

    issues = aggregate_issues(
        static_issues + ast_issues,
        llm_issues,
    )

    summary = ReviewSummary(
        critical=sum(
            issue.severity == Severity.CRITICAL
            for issue in issues
        ),
        high=sum(
            issue.severity == Severity.HIGH
            for issue in issues
        ),
        medium=sum(
            issue.severity == Severity.MEDIUM
            for issue in issues
        ),
        low=sum(
            issue.severity == Severity.LOW
            for issue in issues
        ),
    )

    return ReviewResponse(
        review_id=str(uuid4()),
        summary=summary,
        issues=issues,
    )
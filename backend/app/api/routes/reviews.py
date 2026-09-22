from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.review_repository import (
    get_review,
    save_review,
)

from app.services.github_service import GitHubAPIError

from app.schemas.review import (
    PRReviewRequest,
    ReviewRequest,
)
from app.services.pr_review_service import review_pull_request
from app.services.llm_service import review_with_llm
from app.services.review_service import review_code


router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


def get_llm_reviewer():
    return review_with_llm


@router.post("/")
def create_review(
    request: ReviewRequest,
    db: Session = Depends(get_db),
    llm_reviewer=Depends(get_llm_reviewer),
):
    review = review_code(
        request.code,
        request.language,
        llm_reviewer=llm_reviewer,
    )

    save_review(
        db,
        review,
    )

    return review

@router.get("/{review_id}")
def fetch_review(
    review_id: str,
    db: Session = Depends(get_db),
):
    review = get_review(
        db,
        review_id,
    )

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Review not found.",
        )

    return {
        "id": review.id,
        "created_at": review.created_at,
        "critical": review.critical,
        "high": review.high,
        "medium": review.medium,
        "low": review.low,
        "issues": [
            {
                "id": issue.id,
                "category": issue.category,
                "severity": issue.severity,
                "file": issue.file,
                "line_start": issue.line_start,
                "line_end": issue.line_end,
                "title": issue.title,
                "description": issue.description,
                "suggestion": issue.suggestion,
                "confidence": issue.confidence,
                "source": issue.source,
                "rule_id": issue.rule_id,
                "pr_status": issue.pr_status,
            }
            for issue in review.issues
        ],
    }

@router.post("/github-pr")
def create_pr_review(
    request: PRReviewRequest,
):
    try:
        return review_pull_request(
            owner=request.owner,
            repo=request.repo,
            pull_number=request.pull_number,
            head_sha=request.head_sha,
        )
    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
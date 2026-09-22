from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.review_repository import save_review

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
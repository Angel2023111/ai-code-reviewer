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
from app.repositories.review_repository import (
    save_pull_request_review,
)
from app.repositories.review_repository import (
    get_pull_request_review,
)
from app.db.models import JobStatus
from app.repositories.review_repository import (
    create_review_job,
    get_review_job,
)
from app.schemas.review import (
    ReviewJobRequest,
    ReviewJobResponse,
)
from app.tasks.review_tasks import run_review_job

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
    db: Session = Depends(get_db),
):
    try:
        results = review_pull_request(
            owner=request.owner,
            repo=request.repo,
            pull_number=request.pull_number,
            head_sha=request.head_sha,
        )

        save_pull_request_review(
            db=db,
            owner=request.owner,
            repo=request.repo,
            pull_number=request.pull_number,
            head_sha=request.head_sha,
            results=results,
        )

        return results

    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc



@router.get("/github-pr/{review_id}")
def fetch_pull_request_review(
    review_id: str,
    db: Session = Depends(get_db),
):
    review = get_pull_request_review(
        db,
        review_id,
    )

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Pull request review not found.",
        )

    return {
        "id": review.id,
        "repository_owner": review.repository_owner,
        "repository_name": review.repository_name,
        "pull_number": review.pull_number,
        "head_sha": review.head_sha,
        "created_at": review.created_at,
        "files": [
            {
                "id": file.id,
                "filename": file.filename,
                "language": file.language,
                "changed_lines": file.changed_lines,
                "issues": [
                    {
                        "id": issue.id,
                        "category": issue.category,
                        "severity": issue.severity,
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
                    for issue in file.issues
                ],
            }
            for file in review.files
        ],
    }

@router.post(
    "/jobs",
    response_model=ReviewJobResponse,
)
def create_review_job_endpoint(
    request: ReviewJobRequest,
    db: Session = Depends(get_db),
):
    job = create_review_job(
        db=db,
        job_type="CODE_REVIEW",
    )

    run_review_job.delay(
        job.id,
        request.code,
        request.language,
    )

    return ReviewJobResponse(
        job_id=job.id,
        status=job.status,
    )

@router.get(
    "/jobs/{job_id}",
    response_model=ReviewJobResponse,
)
def get_review_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = get_review_job(
        db=db,
        job_id=job_id,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Review job not found",
        )

    return ReviewJobResponse(
        job_id=job.id,
        status=job.status,
        review_id=job.review_id,
        error_message=job.error_message,
    )


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
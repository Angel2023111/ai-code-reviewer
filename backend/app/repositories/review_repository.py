from sqlalchemy.orm import Session

from app.db.models import Review, ReviewIssue
from app.schemas.review import ReviewResponse

from app.db.models import (
    PullRequestFile,
    PullRequestIssue,
    PullRequestReview,
)
from sqlalchemy.orm import Session, joinedload

from uuid import uuid4

from app.db.models import ReviewJob, JobStatus

def save_review(
    db: Session,
    review_response: ReviewResponse,
) -> Review:
    review = Review(
        id=review_response.review_id,
        critical=review_response.summary.critical,
        high=review_response.summary.high,
        medium=review_response.summary.medium,
        low=review_response.summary.low,
    )

    for issue in review_response.issues:
        review_issue = ReviewIssue(
            category=issue.category.value,
            severity=issue.severity.value,
            file=issue.file,
            line_start=issue.line_start,
            line_end=issue.line_end,
            title=issue.title,
            description=issue.description,
            suggestion=issue.suggestion,
            confidence=issue.confidence,
            source=issue.source,
            rule_id=issue.rule_id,
            pr_status=(
                issue.pr_status.value
                if issue.pr_status is not None
                else None
            ),
        )

        review.issues.append(review_issue)

    db.add(review)
    db.commit()
    db.refresh(review)

    return review


def get_review(
    db: Session,
    review_id: str,
) -> Review | None:
    return db.get(Review, review_id)

def save_pull_request_review(
    db: Session,
    owner: str,
    repo: str,
    pull_number: int,
    head_sha: str,
    results: list[dict],
) -> PullRequestReview:

    from uuid import uuid4

    pull_request_review = PullRequestReview(
        id=str(uuid4()),
        repository_owner=owner,
        repository_name=repo,
        pull_number=pull_number,
        head_sha=head_sha,
    )

    for result in results:
        review: ReviewResponse = result["review"]

        file = PullRequestFile(
            filename=result["filename"],
            language=result["language"],
            changed_lines=str(
                result["changed_lines"]
            ),
        )

        for issue in review.issues:
            pull_request_issue = PullRequestIssue(
                category=issue.category.value,
                severity=issue.severity.value,
                line_start=issue.line_start,
                line_end=issue.line_end,
                title=issue.title,
                description=issue.description,
                suggestion=issue.suggestion,
                confidence=issue.confidence,
                source=issue.source,
                rule_id=issue.rule_id,
                pr_status=(
                    issue.pr_status.value
                    if issue.pr_status is not None
                    else None
                ),
            )

            file.issues.append(pull_request_issue)

        pull_request_review.files.append(file)

    db.add(pull_request_review)
    db.commit()
    db.refresh(pull_request_review)

    return pull_request_review

def get_pull_request_review(
    db: Session,
    review_id: str,
) -> PullRequestReview | None:
    return (
        db.query(PullRequestReview)
        .options(
            joinedload(PullRequestReview.files)
            .joinedload(PullRequestFile.issues)
        )
        .filter(
            PullRequestReview.id == review_id
        )
        .first()
    )

def create_review_job(
    db: Session,
    job_type: str,
) -> ReviewJob:
    job = ReviewJob(
        id=str(uuid4()),
        status=JobStatus.PENDING.value,
        job_type=job_type,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def get_review_job(
    db: Session,
    job_id: str,
) -> ReviewJob | None:
    return db.get(ReviewJob, job_id)


def update_review_job_status(
    db: Session,
    job_id: str,
    status: JobStatus,
) -> ReviewJob | None:
    job = db.get(ReviewJob, job_id)

    if job is None:
        return None

    job.status = status.value

    db.commit()
    db.refresh(job)

    return job


def complete_review_job(
    db: Session,
    job_id: str,
    review_id: str,
) -> ReviewJob | None:
    job = db.get(ReviewJob, job_id)

    if job is None:
        return None

    job.status = JobStatus.COMPLETED.value
    job.review_id = review_id
    job.error_message = None

    db.commit()
    db.refresh(job)

    return job


def fail_review_job(
    db: Session,
    job_id: str,
    error_message: str,
) -> ReviewJob | None:
    job = db.get(ReviewJob, job_id)

    if job is None:
        return None

    job.status = JobStatus.FAILED.value
    job.error_message = error_message

    db.commit()
    db.refresh(job)

    return job

def get_reviews(
    db: Session,
    limit: int = 20,
) -> list[Review]:
    return (
        db.query(Review)
        .order_by(Review.created_at.desc())
        .limit(limit)
        .all()
    )
from app.celery_app import celery_app
from app.db.database import SessionLocal
from app.db.models import JobStatus
from app.repositories.review_repository import (
    complete_review_job,
    fail_review_job,
    get_review_job,
    update_review_job_status,
)
from app.services.review_service import review_code
from app.services.pr_review_service import review_pull_request
from app.services.github_comment_service import (
    format_review_comment,
)

from app.services.github_service import (
    GitHubAPIError,
    post_pull_request_comment,
)
from app.repositories.review_repository import (
            save_pull_request_review,
        )

@celery_app.task
def run_review_job(
    job_id: str,
    code: str,
    language: str,
) -> str:
    db = SessionLocal()

    try:
        job = get_review_job(
            db=db,
            job_id=job_id,
        )

        if job is None:
            raise ValueError(
                f"Review job {job_id} not found"
            )

        update_review_job_status(
            db=db,
            job_id=job_id,
            status=JobStatus.RUNNING,
        )

        review_response = review_code(
            code=code,
            language=language,
        )

        from app.repositories.review_repository import save_review

        save_review(
            db=db,
            review_response=review_response,
        )

        complete_review_job(
            db=db,
            job_id=job_id,
            review_id=review_response.review_id,
        )

        return review_response.review_id

    except Exception as exc:
        db.rollback()

        fail_review_job(
            db=db,
            job_id=job_id,
            error_message=str(exc),
        )

        raise

    finally:
        db.close()

@celery_app.task
def run_pr_review_job(
    job_id: str,
    owner: str,
    repo: str,
    pull_number: int,
    head_sha: str,
) -> str:
    db = SessionLocal()

    try:
        job = get_review_job(
            db=db,
            job_id=job_id,
        )

        if job is None:
            raise ValueError(
                f"Review job {job_id} not found"
            )

        update_review_job_status(
            db=db,
            job_id=job_id,
            status=JobStatus.RUNNING,
        )

        results = review_pull_request(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            head_sha=head_sha,
        )

        

        pull_request_review = save_pull_request_review(
            db=db,
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            head_sha=head_sha,
            results=results,
        )

        for result in results:
            review = result["review"]

            comment_body = format_review_comment(
                review
            )

            try:
                post_pull_request_comment(
                    owner=owner,
                    repo=repo,
                    pull_number=pull_number,
                    body=comment_body,
                )
            except GitHubAPIError:
                # The review itself was successfully
                # generated and persisted. A comment failure
                # should not mark the review job as failed.
                continue

        complete_review_job(
            db=db,
            job_id=job_id,
            review_id=pull_request_review.id,
        )

        return pull_request_review.id

    except Exception as exc:
        db.rollback()

        fail_review_job(
            db=db,
            job_id=job_id,
            error_message=str(exc),
        )

        raise

    finally:
        db.close()
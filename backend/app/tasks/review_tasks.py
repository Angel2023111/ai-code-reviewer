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
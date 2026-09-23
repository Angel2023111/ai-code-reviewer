from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import JobStatus
from app.repositories.review_repository import create_review_job
from app.schemas.review import (
    ReviewResponse,
    ReviewSummary,
)
from app.tasks import review_tasks
from app.repositories.review_repository import get_review_job
from app.tasks.review_tasks import run_pr_review_job

def create_test_session():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(
        bind=engine,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
    )

    return TestingSessionLocal()


def test_run_review_job_completes_successfully(
    monkeypatch,
):
    db = create_test_session()

    job = create_review_job(
        db=db,
        job_type="CODE_REVIEW",
    )

    fake_review = ReviewResponse(
        review_id="review-123",
        summary=ReviewSummary(
            critical=0,
            high=1,
            medium=0,
            low=0,
        ),
        issues=[],
    )

    monkeypatch.setattr(
        review_tasks,
        "SessionLocal",
        lambda: db,
    )

    monkeypatch.setattr(
        review_tasks,
        "review_code",
        lambda code, language: fake_review,
    )

    result = review_tasks.run_review_job.apply(
        args=[
            job.id,
            "print('hello')",
            "python",
        ],
    )

    assert result.get() == "review-123"

    

    updated_job = get_review_job(
        db=db,
        job_id=job.id,
    )

    assert updated_job is not None
    assert updated_job.status == JobStatus.COMPLETED.value
    assert updated_job.review_id == "review-123"
    assert updated_job.error_message is None

    db.close()


def test_run_review_job_marks_job_failed(
    monkeypatch,
):
    db = create_test_session()

    job = create_review_job(
        db=db,
        job_type="CODE_REVIEW",
    )

    monkeypatch.setattr(
        review_tasks,
        "SessionLocal",
        lambda: db,
    )

    def failing_review(code, language):
        raise RuntimeError(
            "Review service failed"
        )

    monkeypatch.setattr(
        review_tasks,
        "review_code",
        failing_review,
    )

    result = review_tasks.run_review_job.apply(
        args=[
            job.id,
            "print('hello')",
            "python",
        ],
    )

    assert result.failed()



    updated_job = get_review_job(
        db=db,
        job_id=job.id,
    )

    assert updated_job is not None
    assert updated_job.status == JobStatus.FAILED.value
    assert (
        updated_job.error_message
        == "Review service failed"
    )

    db.close()


def test_run_review_job_rejects_missing_job(
    monkeypatch,
):
    db = create_test_session()

    monkeypatch.setattr(
        review_tasks,
        "SessionLocal",
        lambda: db,
    )

    result = review_tasks.run_review_job.apply(
        args=[
            "missing-job-id",
            "print('hello')",
            "python",
        ],
    )

    assert result.failed()

    db.close()


def test_run_review_job_persists_review(
    monkeypatch,
):
    db = create_test_session()

    job = create_review_job(
        db=db,
        job_type="CODE_REVIEW",
    )

    fake_review = ReviewResponse(
        review_id="review-456",
        summary=ReviewSummary(
            critical=1,
            high=0,
            medium=0,
            low=0,
        ),
        issues=[],
    )

    monkeypatch.setattr(
        review_tasks,
        "SessionLocal",
        lambda: db,
    )

    monkeypatch.setattr(
        review_tasks,
        "review_code",
        lambda code, language: fake_review,
    )

    result = review_tasks.run_review_job.apply(
        args=[
            job.id,
            "eval(user_input)",
            "python",
        ],
    )

    assert result.get() == "review-456"

    from app.repositories.review_repository import (
        get_review,
    )

    saved_review = get_review(
        db=db,
        review_id="review-456",
    )

    assert saved_review is not None
    assert saved_review.id == "review-456"

    db.close()
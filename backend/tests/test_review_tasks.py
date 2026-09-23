from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
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
from app.services.github_service import (
    GitHubAPIError,
    post_pull_request_comment,
)

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

def test_run_pr_review_job_posts_github_comment(
    monkeypatch,
):
    db = create_test_session()

    job = create_review_job(
        db=db,
        job_type="GITHUB_PR_REVIEW",
    )

    fake_review = ReviewResponse(
        review_id="review-pr-123",
        summary=ReviewSummary(
            critical=0,
            high=1,
            medium=0,
            low=0,
        ),
        issues=[],
    )

    fake_results = [
        {
            "filename": "app.py",
            "language": "python",
            "changed_lines": [10],
            "review": fake_review,
        }
    ]

    monkeypatch.setattr(
        review_tasks,
        "SessionLocal",
        lambda: db,
    )

    monkeypatch.setattr(
        review_tasks,
        "review_pull_request",
        lambda owner, repo, pull_number, head_sha: (
            fake_results
        ),
    )

    monkeypatch.setattr(
        review_tasks,
        "save_pull_request_review",
        lambda db, owner, repo, pull_number, head_sha, results: (
            type(
                "FakePullRequestReview",
                (),
                {"id": "pr-review-123"},
            )()
        ),
    )

    with patch(
        "app.tasks.review_tasks.format_review_comment",
        return_value="## AI Code Review",
    ) as mock_format, patch(
        "app.tasks.review_tasks.post_pull_request_comment",
    ) as mock_comment:

        result = review_tasks.run_pr_review_job.apply(
            args=[
                job.id,
                "test-owner",
                "test-repo",
                42,
                "abc123",
            ],
        )

    assert result.get() == "pr-review-123"

    mock_format.assert_called_once_with(
        fake_review,
    )

    mock_comment.assert_called_once_with(
        owner="test-owner",
        repo="test-repo",
        pull_number=42,
        body="## AI Code Review",
    )

    updated_job = get_review_job(
        db=db,
        job_id=job.id,
    )

    assert updated_job is not None
    assert updated_job.status == JobStatus.COMPLETED.value
    assert updated_job.review_id == "pr-review-123"
    assert updated_job.error_message is None

    db.close()

def test_run_pr_review_job_survives_comment_failure(
    monkeypatch,
):
    db = create_test_session()

    job = create_review_job(
        db=db,
        job_type="GITHUB_PR_REVIEW",
    )

    fake_review = ReviewResponse(
        review_id="review-pr-456",
        summary=ReviewSummary(
            critical=0,
            high=0,
            medium=1,
            low=0,
        ),
        issues=[],
    )

    fake_results = [
        {
            "filename": "app.py",
            "language": "python",
            "changed_lines": [20],
            "review": fake_review,
        }
    ]

    monkeypatch.setattr(
        review_tasks,
        "SessionLocal",
        lambda: db,
    )

    monkeypatch.setattr(
        review_tasks,
        "review_pull_request",
        lambda owner, repo, pull_number, head_sha: (
            fake_results
        ),
    )

    monkeypatch.setattr(
        review_tasks,
        "save_pull_request_review",
        lambda db, owner, repo, pull_number, head_sha, results: (
            type(
                "FakePullRequestReview",
                (),
                {"id": "pr-review-456"},
            )()
        ),
    )

    def failing_comment(
        owner,
        repo,
        pull_number,
        body,
    ):
        raise review_tasks.GitHubAPIError(
            "GitHub comment failed"
        )

    monkeypatch.setattr(
        review_tasks,
        "post_pull_request_comment",
        failing_comment,
    )

    result = review_tasks.run_pr_review_job.apply(
        args=[
            job.id,
            "test-owner",
            "test-repo",
            42,
            "def456",
        ],
    )

    assert result.get() == "pr-review-456"

    updated_job = get_review_job(
        db=db,
        job_id=job.id,
    )

    assert updated_job is not None
    assert updated_job.status == JobStatus.COMPLETED.value
    assert updated_job.review_id == "pr-review-456"
    assert updated_job.error_message is None

    db.close()
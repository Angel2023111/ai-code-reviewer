from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import Review, ReviewIssue
from app.db.models import (
    PullRequestFile,
    PullRequestIssue,
    PullRequestReview,
)

from app.db.models import (
    JobStatus,
    ReviewJob,
)


def test_review_and_issue_models():
    engine = create_engine(
        "sqlite:///:memory:",
    )

    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    review = Review(
        id="test-review-123",
        critical=1,
        high=2,
        medium=1,
        low=0,
    )

    issue = ReviewIssue(
        category="SECURITY",
        severity="HIGH",
        title="Dangerous eval usage",
        description="eval can execute arbitrary code.",
        suggestion="Avoid eval.",
        confidence=0.98,
        source="ast",
        rule_id="dangerous-call",
    )

    review.issues.append(issue)

    session.add(review)
    session.commit()

    saved_review = session.get(
        Review,
        "test-review-123",
    )

    assert saved_review is not None
    assert saved_review.critical == 1
    assert saved_review.high == 2
    assert len(saved_review.issues) == 1

    saved_issue = saved_review.issues[0]

    assert saved_issue.category == "SECURITY"
    assert saved_issue.severity == "HIGH"
    assert saved_issue.confidence == 0.98

    session.close()

def test_pull_request_review_relationships():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
    )

    db = TestingSessionLocal()

    pull_request = PullRequestReview(
        id="pr-review-123",
        repository_owner="Angel2023111",
        repository_name="ai-code-reviewer",
        pull_number=42,
        head_sha="abc123",
    )

    file = PullRequestFile(
        filename="app.py",
        language="python",
        changed_lines="[10, 11, 12]",
    )

    issue = PullRequestIssue(
        category="SECURITY",
        severity="HIGH",
        line_start=10,
        line_end=10,
        title="Dangerous eval usage",
        description="eval can execute arbitrary code.",
        suggestion="Avoid eval.",
        confidence=0.98,
        source="ast",
        rule_id="dangerous-call",
        pr_status="INTRODUCED",
    )

    file.issues.append(issue)
    pull_request.files.append(file)

    db.add(pull_request)
    db.commit()

    saved = db.get(
        PullRequestReview,
        "pr-review-123",
    )

    assert saved is not None
    assert saved.repository_owner == "Angel2023111"
    assert saved.repository_name == "ai-code-reviewer"
    assert saved.pull_number == 42
    assert saved.head_sha == "abc123"

    assert len(saved.files) == 1
    assert saved.files[0].filename == "app.py"

    assert len(saved.files[0].issues) == 1
    assert saved.files[0].issues[0].title == "Dangerous eval usage"
    assert saved.files[0].issues[0].pr_status == "INTRODUCED"

    db.close()

def test_review_job_model():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
    )

    db = TestingSessionLocal()

    job = ReviewJob(
        id="job-123",
        status=JobStatus.PENDING.value,
        job_type="GITHUB_PR_REVIEW",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    assert job.id == "job-123"
    assert job.status == "PENDING"
    assert job.job_type == "GITHUB_PR_REVIEW"
    assert job.error_message is None
    assert job.review_id is None

    db.close()

def test_review_job_status_transition():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
    )

    db = TestingSessionLocal()

    job = ReviewJob(
        id="job-456",
        status=JobStatus.PENDING.value,
        job_type="GITHUB_PR_REVIEW",
    )

    db.add(job)
    db.commit()

    job.status = JobStatus.RUNNING.value
    db.commit()

    db.refresh(job)

    assert job.status == "RUNNING"

    job.status = JobStatus.COMPLETED.value
    job.review_id = "review-123"
    db.commit()

    db.refresh(job)

    assert job.status == "COMPLETED"
    assert job.review_id == "review-123"

    db.close()
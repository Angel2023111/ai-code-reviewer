from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.repositories.review_repository import (
    get_review,
    save_review,
)
from app.repositories.review_repository import (
    save_pull_request_review,
    get_pull_request_review,
)
from app.schemas.review import (
    IssueCategory,
    ReviewIssue,
    ReviewResponse,
    ReviewSummary,
    Severity,
    FindingStatus,
)


def test_save_and_get_review():
    engine = create_engine(
        "sqlite:///:memory:",
    )

    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    db = Session()

    review_response = ReviewResponse(
        review_id="repository-test-123",
        summary=ReviewSummary(
            critical=0,
            high=1,
            medium=1,
            low=0,
        ),
        issues=[
            ReviewIssue(
                category=IssueCategory.SECURITY,
                severity=Severity.HIGH,
                file="app.py",
                line_start=10,
                line_end=10,
                title="Dangerous eval usage",
                description="eval can execute arbitrary code.",
                suggestion="Avoid eval.",
                confidence=0.98,
                source="ast",
                rule_id="dangerous-call",
            ),
            ReviewIssue(
                category=IssueCategory.CODE_QUALITY,
                severity=Severity.MEDIUM,
                file="utils.py",
                line_start=20,
                line_end=25,
                title="Large function",
                description="Function is too large.",
                suggestion="Split the function into smaller functions.",
                confidence=0.85,
                source="ast",
                rule_id="large-function",
            ),
        ],
    )

    saved = save_review(
        db,
        review_response,
    )

    assert saved.id == "repository-test-123"
    assert saved.high == 1
    assert saved.medium == 1
    assert len(saved.issues) == 2

    fetched = get_review(
        db,
        "repository-test-123",
    )

    assert fetched is not None
    assert fetched.id == "repository-test-123"
    assert len(fetched.issues) == 2

    assert fetched.issues[0].category == "SECURITY"
    assert fetched.issues[0].severity == "HIGH"
    assert fetched.issues[0].confidence == 0.98

    db.close()

def test_save_pull_request_review():
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

    review = ReviewResponse(
        review_id="review-123",
        summary=ReviewSummary(
            critical=0,
            high=1,
            medium=0,
            low=0,
        ),
        issues=[
            ReviewIssue(
                category=IssueCategory.SECURITY,
                severity=Severity.HIGH,
                file="app.py",
                line_start=10,
                line_end=10,
                title="Dangerous eval usage",
                description="eval can execute arbitrary code.",
                suggestion="Avoid eval.",
                confidence=0.98,
                source="ast",
                rule_id="dangerous-call",
                pr_status=FindingStatus.INTRODUCED,
            )
        ],
    )

    result = save_pull_request_review(
        db=db,
        owner="Angel2023111",
        repo="ai-code-reviewer",
        pull_number=42,
        head_sha="abc123",
        results=[
            {
                "filename": "app.py",
                "language": "python",
                "changed_lines": [10],
                "review": review,
            }
        ],
    )

    assert result.repository_owner == "Angel2023111"
    assert result.repository_name == "ai-code-reviewer"
    assert result.pull_number == 42
    assert result.head_sha == "abc123"

    assert len(result.files) == 1
    assert result.files[0].filename == "app.py"

    assert len(result.files[0].issues) == 1

    saved_issue = result.files[0].issues[0]

    assert saved_issue.category == "SECURITY"
    assert saved_issue.severity == "HIGH"
    assert saved_issue.pr_status == "INTRODUCED"

    db.close()

def test_save_and_get_pull_request_review():
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

    review = ReviewResponse(
        review_id="review-123",
        summary=ReviewSummary(
            critical=0,
            high=1,
            medium=0,
            low=0,
        ),
        issues=[
            ReviewIssue(
                category=IssueCategory.SECURITY,
                severity=Severity.HIGH,
                file="app.py",
                line_start=10,
                line_end=10,
                title="Dangerous eval usage",
                description="eval can execute arbitrary code.",
                suggestion="Avoid eval.",
                confidence=0.98,
                source="ast",
                rule_id="dangerous-call",
                pr_status=FindingStatus.INTRODUCED,
            )
        ],
    )

    saved = save_pull_request_review(
        db=db,
        owner="Angel2023111",
        repo="ai-code-reviewer",
        pull_number=42,
        head_sha="abc123",
        results=[
            {
                "filename": "app.py",
                "language": "python",
                "changed_lines": [10],
                "review": review,
            }
        ],
    )

    retrieved = get_pull_request_review(
        db=db,
        review_id=saved.id,
    )

    assert retrieved is not None
    assert retrieved.repository_owner == "Angel2023111"
    assert retrieved.repository_name == "ai-code-reviewer"
    assert retrieved.pull_number == 42
    assert retrieved.head_sha == "abc123"

    assert len(retrieved.files) == 1
    assert retrieved.files[0].filename == "app.py"
    assert retrieved.files[0].language == "python"

    assert len(retrieved.files[0].issues) == 1
    assert retrieved.files[0].issues[0].category == "SECURITY"
    assert retrieved.files[0].issues[0].severity == "HIGH"

    db.close()
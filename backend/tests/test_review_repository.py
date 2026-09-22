from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.repositories.review_repository import (
    get_review,
    save_review,
)
from app.schemas.review import (
    IssueCategory,
    ReviewIssue,
    ReviewResponse,
    ReviewSummary,
    Severity,
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
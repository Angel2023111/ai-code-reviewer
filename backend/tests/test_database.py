from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Review, ReviewIssue


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
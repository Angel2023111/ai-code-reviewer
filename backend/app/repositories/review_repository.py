from sqlalchemy.orm import Session

from app.db.models import Review, ReviewIssue
from app.schemas.review import ReviewResponse


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
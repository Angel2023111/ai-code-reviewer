from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    critical: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    high: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    medium: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    low: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    issues: Mapped[list["ReviewIssue"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )


class ReviewIssue(Base):
    __tablename__ = "review_issues"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("reviews.id"),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    file: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    line_start: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    line_end: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    suggestion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    rule_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    pr_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    review: Mapped[Review] = relationship(
        back_populates="issues",
    )
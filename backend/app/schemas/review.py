from enum import Enum

from pydantic import BaseModel, Field


class IssueCategory(str, Enum):
    BUG = "BUG"
    SECURITY = "SECURITY"
    DESIGN = "DESIGN"
    PERFORMANCE = "PERFORMANCE"
    CODE_QUALITY = "CODE_QUALITY"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class FindingStatus(str, Enum):
    INTRODUCED = "INTRODUCED"
    MODIFIED = "MODIFIED"
    PRE_EXISTING = "PRE_EXISTING"


class ReviewRequest(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=100_000,
        description="Source code to review"
    )

    language: str = Field(
        min_length=1,
        max_length=50,
        description="Programming language"
    )

class PRReviewRequest(BaseModel):
    owner: str = Field(
        min_length=1,
        max_length=100,
    )

    repo: str = Field(
        min_length=1,
        max_length=100,
    )

    pull_number: int = Field(
        ge=1,
    )

    head_sha: str = Field(
        min_length=1,
        max_length=100,
    )


class FindingStatus(str, Enum):
    INTRODUCED = "INTRODUCED"
    MODIFIED = "MODIFIED"
    PRE_EXISTING = "PRE_EXISTING"


class ReviewIssue(BaseModel):
    category: IssueCategory
    severity: Severity

    file: str | None
    line_start: int | None
    line_end: int | None

    title: str
    description: str
    suggestion: str

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )
    source: str | None = None
    rule_id: str | None = None
    pr_status: FindingStatus | None = None


class ReviewIssueList(BaseModel):
    issues: list[ReviewIssue]


class ReviewSummary(BaseModel):
    critical: int
    high: int
    medium: int
    low: int


class ReviewResponse(BaseModel):
    review_id: str
    summary: ReviewSummary
    issues: list[ReviewIssue]

class ReviewJobRequest(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=100_000,
        description="Source code to review",
    )

    language: str = Field(
        min_length=1,
        max_length=50,
        description="Programming language",
    )


class ReviewJobResponse(BaseModel):
    job_id: str
    status: str
    review_id: str | None = None
    error_message: str | None = None


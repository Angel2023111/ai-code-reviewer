from fastapi.testclient import TestClient

from app.main import app
from app.api.routes.reviews import get_llm_reviewer

from app.services.github_service import GitHubAPIError

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import Review, ReviewIssue

from app.schemas.review import (
    ReviewResponse,
    ReviewSummary,
)
import pytest

engine = create_engine(
    "sqlite://",
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm_reviewer] = fake_llm_reviewer

    yield

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()



def fake_llm_reviewer():
    return lambda code, language: []


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


client = TestClient(app)




def test_review_endpoint_accepts_valid_request():
    response = client.post(
        "/reviews/",
        json={
            "code": """
def add(a, b):
    return a + b
""",
            "language": "python",
        },
    )

    print(response.json())
    assert response.status_code == 200

    data = response.json()

    assert "review_id" in data
    assert "summary" in data
    assert "issues" in data

    assert isinstance(data["review_id"], str)
    assert isinstance(data["summary"], dict)
    assert isinstance(data["issues"], list)


def test_review_endpoint_rejects_empty_code():
    response = client.post(
        "/reviews/",
        json={
            "code": "",
            "language": "python",
        },
    )

    assert response.status_code == 422


def test_review_endpoint_rejects_missing_language():
    response = client.post(
        "/reviews/",
        json={
            "code": "print('hello')",
        },
    )

    assert response.status_code == 422


def test_review_endpoint_rejects_missing_code():
    response = client.post(
        "/reviews/",
        json={
            "language": "python",
        },
    )

    assert response.status_code == 422

def test_create_pr_review(monkeypatch):
    fake_result = [
    {
        "filename": "app.py",
        "language": "python",
        "changed_lines": [2],
        "review": ReviewResponse(
            review_id="test-review",
            summary=ReviewSummary(
                critical=0,
                high=1,
                medium=0,
                low=0,
            ),
            issues=[],
        ),
    }
]

    def fake_review_pull_request(
        owner,
        repo,
        pull_number,
        head_sha,
    ):
        assert owner == "test-owner"
        assert repo == "test-repo"
        assert pull_number == 42
        assert head_sha == "abc123"

        return fake_result

    monkeypatch.setattr(
        "app.api.routes.reviews.review_pull_request",
        fake_review_pull_request,
    )

    response = client.post(
        "/reviews/github-pr",
        json={
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": 42,
            "head_sha": "abc123",
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "filename": "app.py",
            "language": "python",
            "changed_lines": [2],
            "review": fake_result[0]["review"].model_dump(mode="json"),
        }
    ]

def test_create_pr_review_returns_502_on_github_error(
    monkeypatch,
):
    def fake_review_pull_request(
        owner,
        repo,
        pull_number,
        head_sha,
    ):
        raise GitHubAPIError(
            "GitHub API request failed."
        )

    monkeypatch.setattr(
        "app.api.routes.reviews.review_pull_request",
        fake_review_pull_request,
    )

    response = client.post(
        "/reviews/github-pr",
        json={
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": 42,
            "head_sha": "abc123",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "GitHub API request failed."
    )

def test_create_pr_review_rejects_missing_owner():
    response = client.post(
        "/reviews/github-pr",
        json={
            "repo": "test-repo",
            "pull_number": 42,
            "head_sha": "abc123",
        },
    )

    assert response.status_code == 422

def test_create_pr_review_rejects_invalid_pull_number():
    response = client.post(
        "/reviews/github-pr",
        json={
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": 0,
            "head_sha": "abc123",
        },
    )

    assert response.status_code == 422

def test_create_pr_review_rejects_missing_head_sha():
    response = client.post(
        "/reviews/github-pr",
        json={
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": 42,
        },
    )

    assert response.status_code == 422

def test_get_review():

    
    db = TestingSessionLocal()

    review = Review(
        id="api-review-123",
        critical=0,
        high=1,
        medium=0,
        low=0,
    )

    issue = ReviewIssue(
        category="SECURITY",
        severity="HIGH",
        file="app.py",
        line_start=10,
        line_end=10,
        title="Dangerous eval usage",
        description="eval can execute arbitrary code.",
        suggestion="Avoid eval.",
        confidence=0.98,
        source="ast",
        rule_id="dangerous-call",
    )

    review.issues.append(issue)

    db.add(review)
    db.commit()
    db.close()

    response = client.get(
        "/reviews/api-review-123",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "api-review-123"
    assert data["high"] == 1
    assert len(data["issues"]) == 1
    assert data["issues"][0]["category"] == "SECURITY"

def test_get_review_not_found():

    response = client.get(
        "/reviews/does-not-exist",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found."


def test_get_pull_request_review(monkeypatch):
    review_id = "pr-review-123"

    def fake_get_pull_request_review(
        db,
        review_id,
    ):
        class FakeReview:
            id = review_id
            repository_owner = "test-owner"
            repository_name = "test-repo"
            pull_number = 42
            head_sha = "abc123"
            created_at = None
            files = []

        return FakeReview()

    monkeypatch.setattr(
        "app.api.routes.reviews.get_pull_request_review",
        fake_get_pull_request_review,
    )

    response = client.get(
        f"/reviews/github-pr/{review_id}"
    )

    assert response.status_code == 200

    assert response.json() == {
        "id": review_id,
        "repository_owner": "test-owner",
        "repository_name": "test-repo",
        "pull_number": 42,
        "head_sha": "abc123",
        "created_at": None,
        "files": [],
    }

def test_get_pull_request_review_not_found(monkeypatch):
    def fake_get_pull_request_review(
        db,
        review_id,
    ):
        return None

    monkeypatch.setattr(
        "app.api.routes.reviews.get_pull_request_review",
        fake_get_pull_request_review,
    )

    response = client.get(
        "/reviews/github-pr/nonexistent"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Pull request review not found."
    }
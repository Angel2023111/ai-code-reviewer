from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_github_webhook_accepts_opened_pr():
    response = client.post(
        "/reviews/webhooks/github",
        json={
            "action": "opened",
            "repository": {
                "full_name": "test-owner/test-repo",
            },
            "pull_request": {
                "number": 42,
                "head": {
                    "sha": "abc123",
                },
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "accepted"
    assert data["job_id"]
    assert data["owner"] == "test-owner"
    assert data["repo"] == "test-repo"
    assert data["pull_number"] == 42
    assert data["head_sha"] == "abc123"


def test_github_webhook_accepts_synchronize():
    response = client.post(
        "/reviews/webhooks/github",
        json={
            "action": "synchronize",
            "repository": {
                "full_name": "test-owner/test-repo",
            },
            "pull_request": {
                "number": 42,
                "head": {
                    "sha": "def456",
                },
            },
        },
    )

    assert response.status_code == 200

    assert response.json()["status"] == "accepted"
    assert response.json()["head_sha"] == "def456"


def test_github_webhook_accepts_reopened_pr():
    response = client.post(
        "/reviews/webhooks/github",
        json={
            "action": "reopened",
            "repository": {
                "full_name": "test-owner/test-repo",
            },
            "pull_request": {
                "number": 42,
                "head": {
                    "sha": "abc123",
                },
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_github_webhook_ignores_closed_pr():
    response = client.post(
        "/reviews/webhooks/github",
        json={
            "action": "closed",
            "repository": {
                "full_name": "test-owner/test-repo",
            },
            "pull_request": {
                "number": 42,
                "head": {
                    "sha": "abc123",
                },
            },
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ignored",
        "reason": "Unsupported pull request action",
    }


def test_github_webhook_rejects_missing_repository():
    response = client.post(
        "/reviews/webhooks/github",
        json={
            "action": "opened",
            "pull_request": {
                "number": 42,
                "head": {
                    "sha": "abc123",
                },
            },
        },
    )

    assert response.status_code == 422


def test_github_webhook_rejects_missing_pull_request():
    response = client.post(
        "/reviews/webhooks/github",
        json={
            "action": "opened",
            "repository": {
                "full_name": "test-owner/test-repo",
            },
        },
    )

    assert response.status_code == 422
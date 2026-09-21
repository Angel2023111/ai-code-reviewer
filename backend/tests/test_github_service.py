from unittest.mock import Mock, patch

from app.services.github_service import (
    get_file_contents,
    get_pull_request_files,
    GitHubAPIError,
)

import pytest
import requests

def test_get_pull_request_files():
    fake_files = [
        {
            "filename": "app.py",
            "status": "modified",
            "additions": 5,
            "deletions": 2,
            "changes": 7,
            "patch": "@@ -10,4 +10,7 @@",
        }
    ]

    mock_response = Mock()
    mock_response.json.return_value = fake_files
    mock_response.raise_for_status.return_value = None

    with patch(
        "app.services.github_service.requests.get",
        return_value=mock_response,
    ) as mock_get:

        result = get_pull_request_files(
            owner="test-owner",
            repo="test-repo",
            pull_number=12,
        )

    assert result == fake_files

    mock_get.assert_called_once_with(
        "https://api.github.com/repos/"
        "test-owner/test-repo/pulls/12/files",
        timeout=10,
    )

def test_get_file_contents():
    import base64

    source_code = """def process(data):
    result = eval(data)
    return result
"""

    encoded_content = base64.b64encode(
        source_code.encode("utf-8")
    ).decode("utf-8")

    mock_response = Mock()

    mock_response.json.return_value = {
        "content": encoded_content,
        "encoding": "base64",
    }

    mock_response.raise_for_status.return_value = None

    with patch(
        "app.services.github_service.requests.get",
        return_value=mock_response,
    ) as mock_get:

        result = get_file_contents(
            owner="test-owner",
            repo="test-repo",
            path="app.py",
            ref="abc123",
        )

    assert result == source_code

    mock_get.assert_called_once_with(
        "https://api.github.com/repos/"
        "test-owner/test-repo/contents/app.py",
        params={"ref": "abc123"},
        timeout=10,
    )

def test_get_pull_request_files_raises_on_http_error(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            raise requests.HTTPError("GitHub API error")

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.github_service.requests.get",
        fake_get,
    )

    with pytest.raises(GitHubAPIError):
        get_pull_request_files(
            owner="test-owner",
            repo="test-repo",
            pull_number=1,
        )

def test_get_pull_request_files_raises_rate_limit_error(monkeypatch):
    class FakeResponse:
        status_code = 403

        def raise_for_status(self):
            raise requests.HTTPError(
                "API rate limit exceeded"
            )

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.github_service.requests.get",
        fake_get,
    )

    with pytest.raises(GitHubAPIError):
        get_pull_request_files(
            owner="test-owner",
            repo="test-repo",
            pull_number=1,
        )

def test_get_file_contents_raises_github_api_error(
    monkeypatch,
):
    class FakeResponse:
        def raise_for_status(self):
            raise requests.HTTPError(
                "GitHub API error"
            )

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.github_service.requests.get",
        fake_get,
    )

    with pytest.raises(GitHubAPIError):
        get_file_contents(
            owner="test-owner",
            repo="test-repo",
            path="app.py",
            ref="abc123",
        )
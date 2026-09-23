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

    responses = [
        fake_files,
        [],
    ]

    mock_responses = []

    for data in responses:
        mock_response = Mock()
        mock_response.json.return_value = data
        mock_response.raise_for_status.return_value = None
        mock_responses.append(mock_response)

    with patch(
        "app.services.github_service.requests.get",
        side_effect=mock_responses,
    ) as mock_get:

        result = get_pull_request_files(
            owner="test-owner",
            repo="test-repo",
            pull_number=12,
        )

    assert result == fake_files

    assert mock_get.call_count == 2

    assert mock_get.call_args_list[0].kwargs == {
        "params": {
            "page": 1,
            "per_page": 100,
        },
        "timeout": 10,
    }

    assert mock_get.call_args_list[1].kwargs == {
        "params": {
            "page": 2,
            "per_page": 100,
        },
        "timeout": 10,
    }

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


def test_get_pull_request_files_handles_pagination(
    monkeypatch,
):
    responses = [
        [
            {
                "filename": "file1.py",
                "status": "modified",
            }
        ],
        [
            {
                "filename": "file2.py",
                "status": "modified",
            }
        ],
        [],
    ]

    calls = []

    class FakeResponse:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    def fake_get(url, params=None, timeout=None):
        calls.append(params["page"])

        return FakeResponse(
            responses[params["page"] - 1]
        )

    monkeypatch.setattr(
        "app.services.github_service.requests.get",
        fake_get,
    )

    result = get_pull_request_files(
        owner="test-owner",
        repo="test-repo",
        pull_number=42,
    )

    assert result == [
        {
            "filename": "file1.py",
            "status": "modified",
        },
        {
            "filename": "file2.py",
            "status": "modified",
        },
    ]

    assert calls == [1, 2, 3]


def test_post_pull_request_comment_success(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "id": 123,
                "body": "Test review comment",
            }

    def fake_post(url, json, timeout):
        assert (
            url
            == "https://api.github.com/repos/"
            "test-owner/test-repo/issues/42/comments"
        )
        assert json == {
            "body": "Test review comment",
        }
        assert timeout == 10

        return FakeResponse()

    monkeypatch.setattr(
        "app.services.github_service.requests.post",
        fake_post,
    )

    from app.services.github_service import (
        post_pull_request_comment,
    )

    result = post_pull_request_comment(
        owner="test-owner",
        repo="test-repo",
        pull_number=42,
        body="Test review comment",
    )

    assert result == {
        "id": 123,
        "body": "Test review comment",
    }

def test_post_pull_request_comment_raises_github_api_error(
    monkeypatch,
):
    import requests

    class FakeResponse:
        def raise_for_status(self):
            raise requests.HTTPError("GitHub error")

    def fake_post(url, json, timeout):
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.github_service.requests.post",
        fake_post,
    )

    from app.services.github_service import (
        GitHubAPIError,
        post_pull_request_comment,
    )

    try:
        post_pull_request_comment(
            owner="test-owner",
            repo="test-repo",
            pull_number=42,
            body="Test review comment",
        )
    except GitHubAPIError:
        pass
    else:
        raise AssertionError(
            "Expected GitHubAPIError"
        )
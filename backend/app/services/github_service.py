import requests


GITHUB_API_BASE = "https://api.github.com"

class GitHubAPIError(Exception):
    pass


def get_pull_request_files(
    owner: str,
    repo: str,
    pull_number: int,
) -> list[dict]:

    url = (
        f"{GITHUB_API_BASE}/repos/"
        f"{owner}/{repo}/pulls/{pull_number}/files"
    )

    all_files = []
    page = 1

    while True:
        response = requests.get(
            url,
            params={
                "page": page,
                "per_page": 100,
            },
            timeout=10,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise GitHubAPIError(
                "GitHub API request failed."
            ) from exc

        files = response.json()

        if not files:
            break

        all_files.extend(files)
        page += 1

    return all_files

def get_file_contents(
    owner: str,
    repo: str,
    path: str,
    ref: str,
) -> str:
    url = (
        f"{GITHUB_API_BASE}/repos/"
        f"{owner}/{repo}/contents/{path}"
    )

    response = requests.get(
        url,
        params={"ref": ref},
        timeout=10,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise GitHubAPIError(
            "GitHub API request failed."
        ) from exc

    data = response.json()

    import base64

    return base64.b64decode(
        data["content"]
    ).decode("utf-8")
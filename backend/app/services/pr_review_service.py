from app.services.github_service import (
    get_file_contents,
    get_pull_request_files,
)
from app.services.pr_service import build_pr_file
from app.services.review_service import review_code

from app.services.pr_classification_service import (
    classify_finding,
)

def review_pr_file(
    pr_file: dict,
):
    review = review_code(
        code=pr_file["source_code"],
        language=pr_file["language"],
    )

    for issue in review.issues:
        issue.pr_status = classify_finding(
            issue,
            pr_file["changed_lines"],
        )

    return review


def review_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
    head_sha: str,
) -> list[dict]:

    github_files = get_pull_request_files(
        owner=owner,
        repo=repo,
        pull_number=pull_number,
    )

    results = []

    for github_file in github_files:
        filename = github_file.get("filename")
        patch = github_file.get("patch")

        if not filename or not patch:
            continue

        from app.services.pr_service import get_language

        language = get_language(filename)

        if language is None:
            continue

        source_code = get_file_contents(
            owner=owner,
            repo=repo,
            path=filename,
            ref=head_sha,
        )

        pr_file = build_pr_file(
            filename=filename,
            language=language,
            source_code=source_code,
            patch=patch,
        )

        review = review_pr_file(pr_file)

        results.append(
            {
                "filename": filename,
                "changed_lines": pr_file["changed_lines"],
                "review": review,
            }
        )

    return results
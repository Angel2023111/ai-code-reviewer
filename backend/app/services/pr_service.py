from pathlib import Path

from app.services.diff_service import get_changed_lines


SUPPORTED_EXTENSIONS = {
    ".py": "python",
}


def get_language(filename: str) -> str | None:
    extension = Path(filename).suffix.lower()

    return SUPPORTED_EXTENSIONS.get(extension)


def extract_reviewable_files(
    files: list[dict],
) -> list[dict]:

    reviewable_files = []

    for file in files:
        filename = file.get("filename")
        patch = file.get("patch")

        if not filename or not patch:
            continue

        language = get_language(filename)

        if language is None:
            continue

        reviewable_files.append(
            {
                "filename": filename,
                "language": language,
                "patch": patch,
            }
        )

    return reviewable_files


def build_pr_file(
    filename: str,
    language: str,
    source_code: str,
    patch: str,
) -> dict:
    return {
        "filename": filename,
        "language": language,
        "source_code": source_code,
        "changed_lines": get_changed_lines(patch),
    }
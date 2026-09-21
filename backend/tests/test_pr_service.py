from app.services.pr_service import (
    build_pr_file,
    extract_reviewable_files,
    get_language,
)


def test_get_language_for_python():
    assert get_language("app.py") == "python"


def test_get_language_for_unsupported_file():
    assert get_language("README.md") is None


def test_extract_reviewable_files():
    files = [
        {
            "filename": "app.py",
            "patch": "@@ -1,3 +1,4 @@",
        },
        {
            "filename": "README.md",
            "patch": "@@ -1,2 +1,3 @@",
        },
        {
            "filename": "empty.py",
        },
    ]

    result = extract_reviewable_files(files)

    assert result == [
        {
            "filename": "app.py",
            "language": "python",
            "patch": "@@ -1,3 +1,4 @@",
        }
    ]

def test_build_pr_file():
    source_code = """def process(data):
    value = data.strip()
    result = eval(value)
    return result
"""

    patch = """@@ -1,2 +1,4 @@
 def process(data):
     value = data.strip()
+    result = eval(value)
+    return result
"""

    result = build_pr_file(
        filename="app.py",
        language="python",
        source_code=source_code,
        patch=patch,
    )

    assert result == {
        "filename": "app.py",
        "language": "python",
        "source_code": source_code,
        "changed_lines": [3, 4],
    }
from app.schemas.review import IssueCategory, Severity
from app.services.static_analysis_service import run_static_analysis
from app.services.static_analysis_service import get_bandit_suggestion

def test_unused_variable_is_detected():
    code = """
def test():
    unused = 10
    return 1
"""

    issues = run_static_analysis(code, "python")

    assert any(
        issue.source == "ruff"
        and issue.rule_id == "F841"
        and issue.category == IssueCategory.CODE_QUALITY
        for issue in issues
    )


def test_hardcoded_password_is_detected():
    code = """
def login():
    password = "admin123"
    return password
"""

    issues = run_static_analysis(code, "python")

    assert any(
        issue.source == "bandit"
        and issue.rule_id == "B105"
        and issue.category == IssueCategory.SECURITY
        for issue in issues
    )


def test_eval_is_detected_by_bandit():
    code = """
def run(user_input):
    return eval(user_input)
"""

    issues = run_static_analysis(code, "python")

    assert any(
        issue.source == "bandit"
        and issue.category == IssueCategory.SECURITY
        for issue in issues
    )


def test_non_python_is_ignored():
    code = """
function test() {
    var unused = 10;
}
"""

    issues = run_static_analysis(code, "javascript")

    assert issues == []


def test_clean_python_code_has_no_relevant_findings():
    code = """
def add(a, b):
    return a + b
"""

    issues = run_static_analysis(code, "python")

    assert issues == []


def test_bandit_b404_is_filtered():
    code = """
import subprocess

def run():
    return subprocess.call(["ls"])
"""

    issues = run_static_analysis(code, "python")

    assert not any(
        issue.source == "bandit"
        and issue.rule_id == "B404"
        for issue in issues
    )

def test_bandit_b605_has_actionable_suggestion():
    finding = {
        "test_id": "B605",
    }

    suggestion = get_bandit_suggestion(finding)

    assert "subprocess.run()" in suggestion
    assert "shell=False" in suggestion
    assert "https://" not in suggestion


def test_bandit_b307_has_actionable_suggestion():
    finding = {
        "test_id": "B307",
    }

    suggestion = get_bandit_suggestion(finding)

    assert "eval()" in suggestion
    assert "ast.literal_eval()" in suggestion


def test_unknown_bandit_rule_has_generic_suggestion():
    finding = {
        "test_id": "B999",
    }

    suggestion = get_bandit_suggestion(finding)

    assert suggestion
    assert "secure alternative" in suggestion
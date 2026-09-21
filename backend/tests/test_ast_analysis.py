from app.schemas.review import IssueCategory, Severity
from app.services.ast_analysis_service import run_ast_analysis


def test_eval_is_detected():
    code = """
def run(user_input):
    return eval(user_input)
"""

    issues = run_ast_analysis(code, "python")

    assert len(issues) == 1

    issue = issues[0]

    assert issue.category == IssueCategory.SECURITY
    assert issue.severity == Severity.HIGH
    assert issue.source == "ast"
    assert issue.rule_id == "dangerous-call"
    assert issue.line_start == 3


def test_exec_is_detected():
    code = """
def run(user_input):
    exec(user_input)
"""

    issues = run_ast_analysis(code, "python")

    assert len(issues) == 1

    issue = issues[0]

    assert issue.category == IssueCategory.SECURITY
    assert issue.severity == Severity.HIGH
    assert issue.source == "ast"
    assert issue.rule_id == "dangerous-call"


def test_large_function_is_detected():
    body = "\n".join(
        f"    value_{i} = {i}"
        for i in range(55)
    )

    code = f"""
def large_function():
{body}
"""

    issues = run_ast_analysis(code, "python")

    assert len(issues) == 1

    issue = issues[0]

    assert issue.category == IssueCategory.CODE_QUALITY
    assert issue.severity == Severity.MEDIUM
    assert issue.source == "ast"
    assert issue.rule_id == "large-function"


def test_small_function_is_not_flagged():
    code = """
def small_function():
    x = 10
    return x
"""

    issues = run_ast_analysis(code, "python")

    assert len(issues) == 0


def test_non_python_is_ignored():
    code = """
function test() {
    eval(input);
}
"""

    issues = run_ast_analysis(code, "javascript")

    assert len(issues) == 0


def test_invalid_python_is_ignored():
    code = """
def broken(
"""

    issues = run_ast_analysis(code, "python")

    assert len(issues) == 0
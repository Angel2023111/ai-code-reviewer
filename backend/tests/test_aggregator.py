from app.schemas.review import (
    IssueCategory,
    ReviewIssue,
    Severity,
)
from app.services.aggregator_service import aggregate_issues


def make_issue(
    category,
    severity,
    title,
    description,
    line_start,
    line_end,
    source=None,
    rule_id=None,
    confidence=0.9,
):
    return ReviewIssue(
        category=category,
        severity=severity,
        file=None,
        line_start=line_start,
        line_end=line_end,
        title=title,
        description=description,
        suggestion="Fix the issue.",
        confidence=confidence,
        source=source,
        rule_id=rule_id,
    )


def test_duplicate_eval_is_merged():
    static_issue = make_issue(
        category=IssueCategory.SECURITY,
        severity=Severity.HIGH,
        title="Dangerous use of eval",
        description="Use of eval can execute arbitrary code.",
        line_start=2,
        line_end=2,
        source="ast",
        rule_id="dangerous-call",
    )

    llm_issue = make_issue(
        category=IssueCategory.SECURITY,
        severity=Severity.HIGH,
        title="Use of eval is dangerous",
        description="The eval function may allow arbitrary code execution.",
        line_start=2,
        line_end=2,
        source="llm",
    )

    result = aggregate_issues(
        [static_issue],
        [llm_issue],
    )

    assert len(result) == 1
    assert result[0].category == IssueCategory.SECURITY
    assert result[0].severity == Severity.HIGH


def test_hardcoded_password_is_merged():
    static_issue = make_issue(
        category=IssueCategory.SECURITY,
        severity=Severity.MEDIUM,
        title="Hardcoded password",
        description="Password is hardcoded in source code.",
        line_start=5,
        line_end=5,
        source="bandit",
        rule_id="B105",
    )

    llm_issue = make_issue(
        category=IssueCategory.SECURITY,
        severity=Severity.HIGH,
        title="Hardcoded password in source code",
        description="A plaintext password is stored directly in the code.",
        line_start=5,
        line_end=5,
        source="llm",
    )

    result = aggregate_issues(
        [static_issue],
        [llm_issue],
    )

    assert len(result) == 1
    assert result[0].source == "bandit"
    assert result[0].rule_id == "B105"
    assert result[0].severity == Severity.HIGH


def test_unused_variable_is_merged():
    static_issue = make_issue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.LOW,
        title="Unused variable",
        description="Local variable is assigned but never used.",
        line_start=4,
        line_end=4,
        source="ruff",
        rule_id="F841",
    )

    llm_issue = make_issue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.LOW,
        title="Unused variable",
        description="The variable is assigned but never used.",
        line_start=4,
        line_end=4,
        source="llm",
    )

    result = aggregate_issues(
        [static_issue],
        [llm_issue],
    )

    assert len(result) == 1
    assert result[0].source == "ruff"
    assert result[0].rule_id == "F841"


def test_different_security_rules_are_not_merged():
    bandit_shell = make_issue(
        category=IssueCategory.SECURITY,
        severity=Severity.LOW,
        title="start_process_with_a_shell",
        description="Starting a process through a shell.",
        line_start=7,
        line_end=7,
        source="bandit",
        rule_id="B605",
    )

    bandit_partial_path = make_issue(
        category=IssueCategory.SECURITY,
        severity=Severity.LOW,
        title="start_process_with_partial_path",
        description="Starting a process using a partial executable path.",
        line_start=7,
        line_end=7,
        source="bandit",
        rule_id="B607",
    )

    result = aggregate_issues(
        [bandit_shell, bandit_partial_path],
        [],
    )

    assert len(result) == 2


def test_repeated_ruff_findings_are_consolidated():
    issues = [
        make_issue(
            category=IssueCategory.CODE_QUALITY,
            severity=Severity.LOW,
            title="Unused variable",
            description="Variable is never used.",
            line_start=i,
            line_end=i,
            source="ruff",
            rule_id="F841",
        )
        for i in [2, 3, 4]
    ]

    result = aggregate_issues(
        issues,
        [],
    )

    assert len(result) == 1
    assert result[0].source == "ruff"
    assert result[0].rule_id == "F841"
    assert "3 instances" in result[0].description


def test_unrelated_issues_remain_separate():
    eval_issue = make_issue(
        category=IssueCategory.SECURITY,
        severity=Severity.HIGH,
        title="Dangerous use of eval",
        description="eval can execute arbitrary code.",
        line_start=2,
        line_end=2,
        source="ast",
        rule_id="dangerous-call",
    )

    unused_variable = make_issue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.LOW,
        title="Unused variable",
        description="Variable is never used.",
        line_start=3,
        line_end=3,
        source="ruff",
        rule_id="F841",
    )

    result = aggregate_issues(
        [eval_issue],
        [unused_variable],
    )

    assert len(result) == 2


def test_ast_and_llm_large_function_findings_remain_separate():
    ast_issue = make_issue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.MEDIUM,
        title="Function is excessively large",
        description="The function contains more than 50 lines.",
        line_start=1,
        line_end=53,
        source="ast",
        rule_id="large-function",
    )

    llm_issue = make_issue(
        category=IssueCategory.DESIGN,
        severity=Severity.LOW,
        title="Function is overly large",
        description=(
            "The function is overly large and does not follow "
            "the single responsibility principle."
        ),
        line_start=1,
        line_end=53,
        source="llm",
    )

    result = aggregate_issues(
        [ast_issue],
        [llm_issue],
    )

    assert len(result) == 2

def test_duplicate_ruff_findings_at_same_location_are_merged():
    first = ReviewIssue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.LOW,
        file=None,
        line_start=5,
        line_end=5,
        title="Unused variable",
        description="Variable is never used.",
        suggestion="Remove the variable.",
        confidence=1.0,
        source="ruff",
        rule_id="F841",
    )

    second = ReviewIssue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.LOW,
        file=None,
        line_start=5,
        line_end=5,
        title="Local variable is unused",
        description="Assigned but never used.",
        suggestion="Remove the variable.",
        confidence=1.0,
        source="ruff",
        rule_id="F841",
    )

    result = aggregate_issues(
        static_issues=[first, second],
        llm_issues=[],
    )

    assert len(result) == 1
    assert result[0].source == "ruff"
    assert result[0].rule_id == "F841"
    assert result[0].line_start == 5


def test_os_system_security_findings_are_merged():
    bandit_issue = ReviewIssue(
        category=IssueCategory.SECURITY,
        severity=Severity.HIGH,
        file=None,
        line_start=7,
        line_end=7,
        title="start_process_with_a_shell",
        description=(
            "Starting a process with a shell, possible injection "
            "detected, security issue."
        ),
        suggestion="Use subprocess safely.",
        confidence=0.95,
        source="bandit",
        rule_id="B605",
    )

    llm_issue = ReviewIssue(
        category=IssueCategory.SECURITY,
        severity=Severity.CRITICAL,
        file=None,
        line_start=7,
        line_end=7,
        title="Command injection via os.system",
        description=(
            "`os.system(user_input)` executes the raw string "
            "as a shell command, enabling arbitrary commands."
        ),
        suggestion="Avoid os.system with user-controlled input.",
        confidence=0.99,
        source="llm",
        rule_id=None,
    )

    result = aggregate_issues(
        static_issues=[bandit_issue],
        llm_issues=[llm_issue],
    )

    assert len(result) == 1
    assert result[0].source == "bandit"
    assert result[0].rule_id == "B605"
    assert result[0].severity == Severity.CRITICAL

def test_overlapping_ruff_findings_are_merged():
    first = ReviewIssue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.LOW,
        file=None,
        line_start=4,
        line_end=5,
        title="Unused variables password and unused_value",
        description=(
            "Variables password and unused_value are assigned "
            "but never used."
        ),
        suggestion="Remove unused variables.",
        confidence=1.0,
        source="ruff",
        rule_id="F841",
    )

    second = ReviewIssue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.LOW,
        file=None,
        line_start=5,
        line_end=5,
        title="Local variable unused_value is unused",
        description=(
            "Variable unused_value is assigned but never used."
        ),
        suggestion="Remove the unused variable.",
        confidence=1.0,
        source="ruff",
        rule_id="F841",
    )

    result = aggregate_issues(
        static_issues=[first, second],
        llm_issues=[],
    )

    assert len(result) == 1
    assert result[0].source == "ruff"
    assert result[0].rule_id == "F841"
    assert result[0].line_start == 4
    assert result[0].line_end == 5

def test_f841_is_not_merged_with_security_finding():
    ruff_issue = ReviewIssue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.LOW,
        file=None,
        line_start=4,
        line_end=4,
        title="Local variable `password` is assigned to but never used",
        description="Ruff rule F841 detected this issue.",
        suggestion="Remove the unused variable.",
        confidence=1.0,
        source="ruff",
        rule_id="F841",
    )

    llm_issue = ReviewIssue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.MEDIUM,
        file=None,
        line_start=4,
        line_end=5,
        title="Hard-coded password and unused variable expose sensitive data",
        description=(
            "A plaintext password and an unused variable are defined "
            "inside the function, leaking credentials and adding dead code."
        ),
        suggestion="Remove the hard-coded password and unused variable.",
        confidence=1.0,
        source="llm",
        rule_id=None,
    )

    result = aggregate_issues(
        static_issues=[ruff_issue],
        llm_issues=[llm_issue],
    )

    assert len(result) == 2

def test_merged_issue_preserves_most_specific_line_range():
    ruff_issue = ReviewIssue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.LOW,
        file=None,
        line_start=5,
        line_end=5,
        title="Unused variable `unused_value`",
        description="Ruff rule F841 detected this issue.",
        suggestion="Remove the unused variable.",
        confidence=1.0,
        source="ruff",
        rule_id="F841",
    )

    llm_issue = ReviewIssue(
        category=IssueCategory.CODE_QUALITY,
        severity=Severity.MEDIUM,
        file=None,
        line_start=4,
        line_end=5,
        title="Unused variable",
        description="The variable is assigned but never used.",
        suggestion="Remove the unused variable.",
        confidence=0.9,
        source="llm",
        rule_id=None,
    )

    result = aggregate_issues(
        static_issues=[ruff_issue],
        llm_issues=[llm_issue],
    )

    assert len(result) == 1

    issue = result[0]

    assert issue.line_start == 5
    assert issue.line_end == 5

def test_deterministic_severity_is_preserved_when_merging_llm_issue():
    bandit_issue = ReviewIssue(
        category=IssueCategory.SECURITY,
        severity=Severity.MEDIUM,
        file=None,
        line_start=6,
        line_end=6,
        title="blacklist",
        description="Use of possibly insecure function.",
        suggestion="Avoid eval().",
        confidence=0.95,
        source="bandit",
        rule_id="B307",
    )

    llm_issue = ReviewIssue(
        category=IssueCategory.SECURITY,
        severity=Severity.CRITICAL,
        file=None,
        line_start=6,
        line_end=6,
        title="Use of eval on untrusted input",
        description="This can lead to arbitrary code execution.",
        suggestion="Avoid eval().",
        confidence=1.0,
        source="llm",
        rule_id=None,
    )

    result = aggregate_issues(
        static_issues=[bandit_issue],
        llm_issues=[llm_issue],
    )

    assert len(result) == 1

    issue = result[0]

    assert issue.source == "bandit"
    assert issue.rule_id == "B307"
    assert issue.severity == Severity.CRITICAL
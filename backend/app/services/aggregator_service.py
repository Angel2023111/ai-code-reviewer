from difflib import SequenceMatcher



from app.schemas.review import (
    IssueCategory,
    ReviewIssue,
    Severity,
)


def aggregate_issues(
    static_issues: list[ReviewIssue],
    llm_issues: list[ReviewIssue],
) -> list[ReviewIssue]:

    all_issues = static_issues + llm_issues

    final_issues: list[ReviewIssue] = []

    for issue in all_issues:

        duplicate_index = find_duplicate(
            issue,
            final_issues,
        )

        if duplicate_index is None:
            final_issues.append(issue)
        else:
            final_issues[duplicate_index] = merge_issues(
                final_issues[duplicate_index],
                issue,
            )

    return consolidate_ruff_findings(final_issues)


def find_duplicate(
    issue: ReviewIssue,
    existing_issues: list[ReviewIssue],
) -> int | None:

    for index, existing in enumerate(existing_issues):

        if issue.category != existing.category:
            continue

        semantic_match = same_issue_semantics(
            issue,
            existing,
        )

        if not semantic_match:
            continue

        # Explicit cross-analyzer rule mappings are strong enough
        # to tolerate slightly different reported line numbers.
        if is_strong_cross_analyzer_match(issue, existing):
            return index

        # Otherwise require overlapping source locations.
        if lines_overlap(issue, existing):
            return index

    return None

def matches_deterministic_rule(
    rule_source: str,
    rule_id: str,
    issue: ReviewIssue,
) -> bool:

    text = (
        f"{issue.title} {issue.description}"
    ).lower()

    if rule_source == "ruff" and rule_id == "F841":

        unused_variable_terms = [
            "unused variable",
            "unused local variable",
            "assigned but never used",
            "variable is never used",
        ]

        # If the finding also describes a security issue,
        # do not treat it as a pure F841 finding.
        security_terms = [
            "password",
            "credential",
            "secret",
            "sensitive data",
            "hardcoded",
            "hard-coded",
        ]

        has_unused_variable = any(
            term in text
            for term in unused_variable_terms
        )

        has_security_context = any(
            term in text
            for term in security_terms
        )

        return (
            has_unused_variable
            and not has_security_context
        )

    if rule_source == "bandit" and rule_id == "B105":

        return any(
            term in text
            for term in [
                "hardcoded password",
                "hard-coded password",
                "hardcoded credential",
                "hard-coded credential",
                "plaintext password",
                "plain text password",
            ]
        )
    if rule_source == "bandit" and rule_id == "B307":

        return any(
            term in text
            for term in [
                "eval",
                "exec",
                "arbitrary code",
                "code execution",
            ]
        )

    if rule_source == "bandit" and rule_id == "B605":

        return any(
            term in text
            for term in [
                "os.system",
                "shell command",
                "command injection",
                "shell execution",
            ]
        )

    return False

def same_issue_semantics(
    first: ReviewIssue,
    second: ReviewIssue,
    allow_without_line_overlap: bool = False,
) -> bool:

    strong_rule_match = (
        (first.source == "ruff" and first.rule_id == "F841")
        or
        (second.source == "ruff" and second.rule_id == "F841")
        or
        (first.source == "bandit" and first.rule_id == "B105")
        or
        (second.source == "bandit" and second.rule_id == "B105")
    )

    if not allow_without_line_overlap and strong_rule_match:
        # The normal caller already verified line overlap.
        pass

    if (
        first.source is not None
        and second.source is not None
        and first.source == second.source
        and first.rule_id is not None
        and second.rule_id is not None
        and first.rule_id != second.rule_id
    ):
        return False

    if (
        first.source in {"ruff", "bandit", "ast"}
        and second.source == first.source
        and first.rule_id == second.rule_id
    ):
        return True

    first_text = (
        f"{first.title} {first.description}"
    ).lower()

    second_text = (
        f"{second.title} {second.description}"
    ).lower()

    # ---------------------------------------------------------
    # Deterministic rule equivalence
    # ---------------------------------------------------------

        # ---------------------------------------------------------
    # Deterministic rule equivalence
    # ---------------------------------------------------------

    deterministic_rules = [
        ("ruff", "F841"),
        ("bandit", "B105"),
        ("bandit", "B307"),
        ("bandit", "B605"),
    ]

    for source, rule_id in deterministic_rules:

        first_is_rule = (
            first.source == source
            and first.rule_id == rule_id
        )

        second_is_rule = (
            second.source == source
            and second.rule_id == rule_id
        )

        if first_is_rule and not second_is_rule:
            if (
                lines_overlap(first, second)
                and matches_deterministic_rule(
                    source,
                    rule_id,
                    second,
                )
            ):
                return True

        if second_is_rule and not first_is_rule:
            if (
                lines_overlap(first, second)
                and matches_deterministic_rule(
                    source,
                    rule_id,
                    first,
                )
            ):
                return True

    # ---------------------------------------------------------
    # Security issue equivalence
    # ---------------------------------------------------------

        security_patterns = [
        {
            "name": "shell_command_injection",
            "keywords": [
                "shell=true",
                "command injection",
                "os.system",
                "shell command",
                "shell execution",
                "start process with a shell",
                "starting a process with a shell",
                "process with a shell",
            ],
        },
        {
            "name": "hardcoded_credential",
            "keywords": [
                "hardcoded password",
                "hard-coded password",
                "hardcoded sensitive",
                "hard-coded sensitive",
                "plaintext password",
                "plain text password",
                "credential",
            ],
        },
        {
            "name": "dangerous_code_execution",
            "keywords": [
                "eval",
                "exec",
                "arbitrary code",
                "code execution",
            ],
        },
    ]

    if first.category == IssueCategory.SECURITY:

        for pattern in security_patterns:

            first_matches = sum(
                keyword in first_text
                for keyword in pattern["keywords"]
            )

            second_matches = sum(
                keyword in second_text
                for keyword in pattern["keywords"]
            )

            if first_matches >= 1 and second_matches >= 1:
                return True

    # ---------------------------------------------------------
    # Code-quality equivalence
    # ---------------------------------------------------------

    quality_patterns = [
        [
            "unused import",
            "imported but unused",
        ],
    ]

    if first.category == IssueCategory.CODE_QUALITY:

        for pattern in quality_patterns:

            first_matches = sum(
                keyword in first_text
                for keyword in pattern
            )

            second_matches = sum(
                keyword in second_text
                for keyword in pattern
            )

            if first_matches >= 1 and second_matches >= 1:
                return True

    # ---------------------------------------------------------
    # General text similarity fallback
    # ---------------------------------------------------------

    similarity = description_similarity(
        first,
        second,
    )

    return similarity >= 0.60


def lines_overlap(
    first: ReviewIssue,
    second: ReviewIssue,
) -> bool:

    if first.line_start is None or second.line_start is None:
        return False

    first_end = first.line_end or first.line_start
    second_end = second.line_end or second.line_start

    return (
        first.line_start <= second_end
        and second.line_start <= first_end
    )


def description_similarity(
    first: ReviewIssue,
    second: ReviewIssue,
) -> float:

    first_text = (
        f"{first.title} {first.description}"
    ).lower()

    second_text = (
        f"{second.title} {second.description}"
    ).lower()

    return SequenceMatcher(
        None,
        first_text,
        second_text,
    ).ratio()

def min_line_start(
    first: int | None,
    second: int | None,
) -> int | None:

    values = [
        value
        for value in (first, second)
        if value is not None
    ]

    if not values:
        return None

    return min(values)


def max_line_end(
    first: int | None,
    second: int | None,
) -> int | None:

    values = [
        value
        for value in (first, second)
        if value is not None
    ]

    if not values:
        return None

    return max(values)

def merge_issues(
    first_issue: ReviewIssue,
    second_issue: ReviewIssue,
) -> ReviewIssue:

    

    # Prefer the issue with more specific deterministic metadata.
    if (
        first_issue.source is not None
        and first_issue.rule_id is not None
    ):
        source = first_issue.source
        rule_id = first_issue.rule_id

    elif (
        second_issue.source is not None
        and second_issue.rule_id is not None
    ):
        source = second_issue.source
        rule_id = second_issue.rule_id

    else:
        source = (
            first_issue.source
            if first_issue.source is not None
            else second_issue.source
        )

        rule_id = (
            first_issue.rule_id
            if first_issue.rule_id is not None
            else second_issue.rule_id
        )

    if first_issue.source in {"ruff", "bandit", "ast"}:
        line_start = first_issue.line_start
        line_end = first_issue.line_end

    elif second_issue.source in {"ruff", "bandit", "ast"}:
        line_start = second_issue.line_start
        line_end = second_issue.line_end

    else:
        line_start = min_line_start(
            first_issue.line_start,
            second_issue.line_start,
        )

        line_end = max_line_end(
            first_issue.line_end,
            second_issue.line_end,
        )

    severity_rank = {
        Severity.CRITICAL: 4,
        Severity.HIGH: 3,
        Severity.MEDIUM: 2,
        Severity.LOW: 1,
    }



    severity = max(
        [first_issue.severity, second_issue.severity],
        key=lambda value: severity_rank[value],
    )

    return ReviewIssue(
        category=first_issue.category,

        severity=severity,

        file=(
            second_issue.file
            if second_issue.file is not None
            else first_issue.file
        ),
        line_start=line_start,
        line_end=line_end,

        title=(
            second_issue.title
            if second_issue.source == "llm"
            else first_issue.title
        ),

        description=(
            second_issue.description
            if second_issue.source == "llm"
            else first_issue.description
        ),

        suggestion=(
            second_issue.suggestion
            if second_issue.source == "llm"
            else first_issue.suggestion
        ),

        confidence=max(
            first_issue.confidence,
            second_issue.confidence,
        ),

        source=source,
        rule_id=rule_id,

        pr_status=(
            first_issue.pr_status
            if first_issue.pr_status is not None
            else second_issue.pr_status
        ),
    )


def max_severity(
    first,
    second,
):
    severity_order = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }

    if severity_order[first.value] >= severity_order[second.value]:
        return first

    return second

def consolidate_ruff_findings(
    issues: list[ReviewIssue],
) -> list[ReviewIssue]:

    result: list[ReviewIssue] = []

    grouped: dict[str, list[ReviewIssue]] = {}

    for issue in issues:

        if (
            issue.source == "ruff"
            and issue.rule_id is not None
        ):
            key = f"{issue.category.value}:{issue.rule_id}"

            grouped.setdefault(key, []).append(issue)

        else:
            result.append(issue)

    for key, findings in grouped.items():

        rule_id = findings[0].rule_id

        # -----------------------------------------------------
        # First remove duplicate/overlapping findings for the
        # same Ruff rule.
        #
        # Example:
        #   F841 line 5
        #   F841 line 5
        #
        # becomes one finding.
        #
        # But:
        #   F841 line 5
        #   F841 line 10
        #
        # remains two findings.
        # -----------------------------------------------------

        distinct_findings: list[ReviewIssue] = []

        for finding in findings:

            duplicate = False

            for existing in distinct_findings:

                if lines_overlap(finding, existing):
                    duplicate = True
                    break

            if not duplicate:
                distinct_findings.append(finding)

        findings = distinct_findings

        # -----------------------------------------------------
        # Keep separate findings when there are only a few
        # distinct locations.
        # -----------------------------------------------------

        if len(findings) < 3:
            result.extend(findings)
            continue

        # -----------------------------------------------------
        # Consolidate repeated Ruff findings when there are
        # many distinct locations.
        # -----------------------------------------------------

        line_numbers = [
            issue.line_start
            for issue in findings
            if issue.line_start is not None
        ]

        if line_numbers:
            line_start = min(line_numbers)
            line_end = max(line_numbers)
        else:
            line_start = None
            line_end = None

        result.append(
            ReviewIssue(
                category=findings[0].category,
                severity=max(
                    (issue.severity for issue in findings),
                    key=lambda severity: {
                        Severity.LOW: 1,
                        Severity.MEDIUM: 2,
                        Severity.HIGH: 3,
                        Severity.CRITICAL: 4,
                    }[severity],
                ),
                file=findings[0].file,
                line_start=line_start,
                line_end=line_end,
                title=(
                    f"Multiple instances of Ruff rule {rule_id}"
                ),
                description=(
                    f"{len(findings)} instances of Ruff rule "
                    f"{rule_id} were detected in this code."
                ),
                suggestion=(
                    "Review and address the repeated instances of "
                    f"Ruff rule {rule_id}."
                ),
                confidence=1.0,
                source="ruff",
                rule_id=rule_id,
            )
        )

    return result


def is_strong_cross_analyzer_match(
    first: ReviewIssue,
    second: ReviewIssue,
) -> bool:

    rule_mappings = {
        ("ruff", "F841"): {
            "unused variable",
            "unused local variable",
            "assigned but never used",
            "variable is never used",
            "unused variable assignments",
        },

        ("bandit", "B105"): {
            "hardcoded password",
            "hard-coded password",
            "hardcoded credential",
            "hard-coded credential",
            "plaintext password",
            "plain text password",
        },

        ("bandit", "B307"): {
            "eval(",
            "use of eval",
            "calls eval",
            "eval function",
        },

        ("bandit", "B605"): {
            "os.system",
            "start_process_with_a_shell",
            "starting a process with a shell",
        },
    }

    first_text = (
        f"{first.title} {first.description}"
    ).lower()

    second_text = (
        f"{second.title} {second.description}"
    ).lower()

    for (source, rule_id), keywords in rule_mappings.items():

        first_is_rule = (
            first.source == source
            and first.rule_id == rule_id
        )

        second_is_rule = (
            second.source == source
            and second.rule_id == rule_id
        )

        if first_is_rule and not second_is_rule:
            if any(keyword in second_text for keyword in keywords):
                return True

        if second_is_rule and not first_is_rule:
            if any(keyword in first_text for keyword in keywords):
                return True

    return False
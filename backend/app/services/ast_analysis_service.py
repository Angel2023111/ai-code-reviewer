import ast

from app.schemas.review import (
    IssueCategory,
    ReviewIssue,
    Severity,
)


class ASTAnalyzer(ast.NodeVisitor):

    def __init__(self):
        self.issues: list[ReviewIssue] = []

    def visit_Call(self, node: ast.Call):
        self.check_dangerous_call(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.check_function_complexity(node)
        self.generic_visit(node)

    def check_dangerous_call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec"}:
                self.issues.append(
                    ReviewIssue(
                        category=IssueCategory.SECURITY,
                        severity=Severity.HIGH,
                        file=None,
                        line_start=node.lineno,
                        line_end=node.end_lineno,
                        title=f"Use of dangerous function: {node.func.id}",
                        description=(
                            f"The `{node.func.id}()` function can execute "
                            "arbitrary Python code and may allow code "
                            "execution when given untrusted input."
                        ),
                        suggestion=(
                            f"Avoid `{node.func.id}()` with untrusted input. "
                            "Use a safer, explicitly validated alternative."
                        ),
                        confidence=0.98,
                        source="ast",
                        rule_id="dangerous-call",
                    )
                )

    def check_function_complexity(self, node: ast.FunctionDef):
        if node.end_lineno is None:
            return

        function_length = (
            node.end_lineno - node.lineno + 1
        )

        if function_length > 50:
            self.issues.append(
                ReviewIssue(
                    category=IssueCategory.CODE_QUALITY,
                    severity=Severity.MEDIUM,
                    file=None,
                    line_start=node.lineno,
                    line_end=node.end_lineno,
                    title="Function is excessively large",
                    description=(
                        f"The function `{node.name}` contains approximately "
                        f"{function_length} lines of code. Large functions "
                        "are harder to understand, test, and maintain."
                    ),
                    suggestion=(
                        "Consider splitting the function into smaller "
                        "functions with clear responsibilities."
                    ),
                    confidence=0.90,
                    source="ast",
                    rule_id="large-function",
                )
            )


def run_ast_analysis(
    code: str,
    language: str,
) -> list[ReviewIssue]:

    if language.lower() != "python":
        return []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    analyzer = ASTAnalyzer()
    analyzer.visit(tree)

    return analyzer.issues
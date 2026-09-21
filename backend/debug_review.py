from app.services.static_analysis_service import run_static_analysis
from app.services.ast_analysis_service import run_ast_analysis

code = """import os

def process(user_input):
    password = "secret123"
    unused_value = 42
    result = eval(user_input)
    os.system(user_input)
    return result
"""

print("=== STATIC ===")

for issue in run_static_analysis(code, "python"):
    print(issue.model_dump())

print("\n=== AST ===")

for issue in run_ast_analysis(code, "python"):
    print(issue.model_dump())
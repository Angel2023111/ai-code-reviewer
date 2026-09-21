from openai import OpenAI, APIError, APITimeoutError, RateLimitError
import json

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.schemas.review import ReviewIssueList


client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    timeout=30.0,
    max_retries=2,
)


SYSTEM_PROMPT = """
You are an expert software engineer performing automated code review.

Your job is to identify real, actionable problems in the provided source code.

Analyze the code for:

1. BUG
   - Incorrect logic
   - Runtime errors
   - Incorrect edge-case handling
   - Incorrect assumptions

2. SECURITY
   - Injection vulnerabilities
   - Authentication/authorization problems
   - Sensitive data exposure
   - Unsafe input handling
   - Insecure configuration

3. DESIGN
   - Poor separation of responsibilities
   - Strong coupling
   - Poor abstractions
   - Difficult-to-maintain architecture

4. PERFORMANCE
   - Unnecessary expensive operations
   - Inefficient algorithms
   - Repeated computation
   - Obvious scalability problems

5. CODE_QUALITY
   - Error-prone code
   - Poor maintainability
   - Duplicated logic
   - Misleading naming
   - Dead or unnecessary code

IMPORTANT REVIEW RULES:

- Only report issues that are reasonably supported by the code.
- Do NOT invent hypothetical problems without evidence.
- Do NOT report stylistic preferences as bugs.
- Prefer fewer high-quality findings over many weak findings.
- Explain the specific reason the code is problematic.
- Provide a concrete fix or improvement.
- Identify the exact line when possible.
- If an exact line cannot be determined, use null.
- Severity should reflect the realistic impact of the issue.
- Confidence must represent how certain you are that the issue is real.
- Do NOT report the same issue multiple times.
- Each reported issue must represent exactly one independent problem or root cause.
- Do NOT combine multiple unrelated problems into one issue.
- If two problems occur on different lines or have different root causes, report them as separate issues.
- For example, a hard-coded password and an unused variable must be reported as two separate issues.
- Keep each issue focused so that it can be independently deduplicated against static-analysis findings.
- Do not use a single issue to describe multiple vulnerabilities, bugs, or code-quality problems.

Severity guidelines:

Severity guidelines:

CRITICAL:
Issues that could cause severe security impact, data loss,
or catastrophic system behavior.

HIGH:
Serious bugs or security vulnerabilities that can significantly
affect correctness or system behavior.

MEDIUM:
Meaningful bugs, performance problems, or maintainability issues
that should be addressed.

LOW:
Minor issues with limited impact.

Return only actionable findings.
"""


REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "BUG",
                            "SECURITY",
                            "DESIGN",
                            "PERFORMANCE",
                            "CODE_QUALITY"
                        ]
                    },
                    "severity": {
                        "type": "string",
                        "enum": [
                            "CRITICAL",
                            "HIGH",
                            "MEDIUM",
                            "LOW"
                        ]
                    },
                    "file": {
                        "type": ["string", "null"]
                    },
                    "line_start": {
                        "type": ["integer", "null"]
                    },
                    "line_end": {
                        "type": ["integer", "null"]
                    },
                    "title": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    },
                    "suggestion": {
                        "type": "string"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    }
                },
                "required": [
                    "category",
                    "severity",
                    "file",
                    "line_start",
                    "line_end",
                    "title",
                    "description",
                    "suggestion",
                    "confidence"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": ["issues"],
    "additionalProperties": False
}

def parse_llm_response(content: str) -> list:
    if not content:
        raise RuntimeError(
            "LLM returned an empty response."
        )

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "LLM returned invalid JSON."
        ) from exc

    try:
        validated = ReviewIssueList.model_validate(result)
    except Exception as exc:
        raise RuntimeError(
            "LLM returned an invalid review format."
        ) from exc

    issues = validated.issues

    for issue in issues:
        issue.source = "llm"

    return issues

def review_with_llm(code: str, language: str) -> list:

    user_prompt = (
        f"Review the following {language} code.\n\n"
        f"```{language}\n"
        f"{code}\n"
        f"```\n\n"
        "Return all meaningful issues you find."
    )

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "code_review",
                    "strict": True,
                    "schema": REVIEW_SCHEMA,
                },
            },
        )

    except RateLimitError as exc:
        raise RuntimeError(
            "LLM rate limit exceeded. Please try again later."
        ) from exc

    except APITimeoutError as exc:
        raise RuntimeError(
            "LLM request timed out. Please try again."
        ) from exc

    except APIError as exc:
        raise RuntimeError(
            "LLM provider returned an API error."
        ) from exc

    content = response.choices[0].message.content

    return parse_llm_response(content)
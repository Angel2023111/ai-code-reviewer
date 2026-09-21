import re


HUNK_HEADER_PATTERN = re.compile(
    r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@"
)


def parse_patch(patch: str) -> list[dict]:
    lines = patch.splitlines()

    parsed_lines = []

    current_line = None

    for line in lines:

        if line.startswith("@@"):
            match = HUNK_HEADER_PATTERN.match(line)

            if match is None:
                continue

            current_line = int(match.group(1))
            continue

        if current_line is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            parsed_lines.append(
                {
                    "line_number": current_line,
                    "content": line[1:],
                    "is_added": True,
                }
            )

            current_line += 1

        elif line.startswith("-") and not line.startswith("---"):
            # Deleted lines do not exist in the new file,
            # so they do not advance the new-file line number.
            continue

        else:
            parsed_lines.append(
                {
                    "line_number": current_line,
                    "content": line[1:] if line.startswith(" ") else line,
                    "is_added": False,
                }
            )

            current_line += 1

    return parsed_lines

def get_changed_lines(
    patch: str,
) -> list[int]:
    lines = patch.splitlines()

    changed_lines = []

    current_line = None

    for line in lines:

        if line.startswith("@@"):
            match = HUNK_HEADER_PATTERN.match(line)

            if match is None:
                continue

            current_line = int(match.group(1))
            continue

        if current_line is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            changed_lines.append(current_line)
            current_line += 1

        elif line.startswith("-") and not line.startswith("---"):
            # Deleted lines do not exist in the new file.
            continue

        else:
            current_line += 1

    return changed_lines

def build_reviewable_code(
    parsed_lines: list[dict],
) -> tuple[str, dict[int, int]]:
    code_lines = []
    line_mapping = {}

    for index, item in enumerate(parsed_lines, start=1):
        code_lines.append(item["content"])
        line_mapping[index] = item["line_number"]

    return "\n".join(code_lines), line_mapping
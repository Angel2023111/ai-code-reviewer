from app.services.diff_service import (
    build_reviewable_code,
    get_changed_lines,
    parse_patch,
)


def test_parse_added_lines():
    patch = """@@ -10,3 +10,5 @@
 def process(data):
     value = data.strip()
+    result = eval(value)
+    return result
"""

    result = parse_patch(patch)

    assert result == [
        {
            "line_number": 10,
            "content": "def process(data):",
            "is_added": False,
        },
        {
            "line_number": 11,
            "content": "    value = data.strip()",
            "is_added": False,
        },
        {
            "line_number": 12,
            "content": "    result = eval(value)",
            "is_added": True,
        },
        {
            "line_number": 13,
            "content": "    return result",
            "is_added": True,
        },
    ]


def test_deleted_lines_do_not_advance_new_file_line_number():
    patch = """@@ -10,4 +10,3 @@
 def process(data):
-    old_value = data
     value = data.strip()
+    return value
"""

    result = parse_patch(patch)

    assert result == [
        {
            "line_number": 10,
            "content": "def process(data):",
            "is_added": False,
        },
        {
            "line_number": 11,
            "content": "    value = data.strip()",
            "is_added": False,
        },
        {
            "line_number": 12,
            "content": "    return value",
            "is_added": True,
        },
    ]

def test_parse_multiple_hunks():
    patch = """@@ -10,3 +10,4 @@
 def first():
     value = 1
+    return value
@@ -30,3 +31,4 @@
 def second():
     value = 2
+    return value
"""

    result = parse_patch(patch)

    assert result == [
        {
            "line_number": 10,
            "content": "def first():",
            "is_added": False,
        },
        {
            "line_number": 11,
            "content": "    value = 1",
            "is_added": False,
        },
        {
            "line_number": 12,
            "content": "    return value",
            "is_added": True,
        },
        {
            "line_number": 31,
            "content": "def second():",
            "is_added": False,
        },
        {
            "line_number": 32,
            "content": "    value = 2",
            "is_added": False,
        },
        {
            "line_number": 33,
            "content": "    return value",
            "is_added": True,
        },
    ]

def test_build_reviewable_code():
    parsed_lines = [
        {
            "line_number": 20,
            "content": "def process(data):",
            "is_added": False,
        },
        {
            "line_number": 21,
            "content": "    result = eval(data)",
            "is_added": True,
        },
        {
            "line_number": 22,
            "content": "    return result",
            "is_added": True,
        },
    ]

    code, line_mapping = build_reviewable_code(
        parsed_lines
    )

    assert code == (
        "def process(data):\n"
        "    result = eval(data)\n"
        "    return result"
    )

    assert line_mapping == {
        1: 20,
        2: 21,
        3: 22,
    }

def test_get_changed_lines():
    patch = """@@ -10,3 +10,5 @@
 def process(data):
     value = data.strip()
+    result = eval(value)
+    return result
"""

    result = get_changed_lines(patch)

    assert result == [12, 13]

def test_get_changed_lines_multiple_hunks():
    patch = """@@ -10,3 +10,4 @@
 def first():
     value = 1
+    return value
@@ -30,3 +31,4 @@
 def second():
     value = 2
+    return value
"""

    result = get_changed_lines(patch)

    assert result == [12, 33]

def test_get_changed_lines_ignores_deleted_lines():
    patch = """@@ -10,4 +10,3 @@
 def process(data):
-    old_value = data
     value = data.strip()
+    return value
"""

    result = get_changed_lines(patch)

    assert result == [12]
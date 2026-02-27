import re

with open("sql_compare.py", "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

# Find def tokenize
idx = -1
for i, line in enumerate(lines):
    if line.strip().startswith("def tokenize(sql: str):"):
        idx = i
        break

if idx != -1:
    print(f"Found tokenize at line {idx+1}")
    regex_code = [
        'TOKEN_REGEX = re.compile(',
        '    r"""',
        "    (?:'(?:(?:''|[^'])*?)')            # single-quoted string",
        '  | (?:(?:(?:\\bE)?")(?:(?:""|[^"])*?)")  # double-quoted string (allow E"..." too)',
        '  | (?:(?:\\[(?:[^\\]]*?)\\]))                # [bracketed] identifier', # Need to escape [ and ] in regex string? No, raw string. But in python list string?
        # Wait, I am writing a python script that writes python code.
        # simpler to just read the regex from a variable.
    ]

    # Let's use a simpler way.
    regex_block = r'''TOKEN_REGEX = re.compile(
    r"""
    (?:'(?:(?:''|[^'])*?)')            # single-quoted string
  | (?:(?:(?:\bE)?")(?:(?:""|[^"])*?)")  # double-quoted string (allow E"..." too)
  | (?:\[(?:[^\]]*?)\])                # [bracketed] identifier
  | (?:`(?:[^`]*?)`)                   # `backticked` identifier
  | (?:[A-Z_][A-Z0-9_\$]*\b)           # identifiers/keywords (after uppercasing)
  | (?:[0-9]+\.[0-9]+|[0-9]+)          # numbers
  | (?:<=|>=|<>|!=|:=|->|::)           # multi-char operators
  | (?:[(),=*\/\+\-<>\.%])             # single-char tokens
  | (?:\.)                             # dot
  | (?:\s+)                            # whitespace (filtered out)
    """,
    re.VERBOSE | re.IGNORECASE,
)'''

    lines.insert(idx, regex_block)

    with open("sql_compare.py", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("Restored TOKEN_REGEX")
else:
    print("Could not find tokenize function")

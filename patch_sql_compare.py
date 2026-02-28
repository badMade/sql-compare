import re

with open('sql_compare.py', 'r') as f:
    content = f.read()

# Create the CLAUSE_SCANNER_RE definition
scanner_re_def = """
terminators_pattern = "|".join(r"\\b" + re.sub(r"\\s+", r"\\\\s+", term) + r"\\b" for term in SQL_CLAUSE_TERMINATORS)
CLAUSE_SCANNER_RE = re.compile(
    r\"\"\"
    (?:'(?:(?:''|[^'])*?)')               # single-quoted string
  | (?:(?:(?:\\bE)?\")(?:(?:\"\"|[^\"])*?)\")   # double-quoted string (allow E\"...\")
  | (?:\\[(?:[^\\]]*?)\\])                   # [bracketed] identifier
  | (?:`(?:[^`]*?)`)                      # `backticked` identifier
  | \\(                                    # open paren
  | \\)                                    # close paren
  | (?:\"\"\" + terminators_pattern + r\"\"\")  # clause terminators
    \"\"\",
    re.VERBOSE | re.IGNORECASE
)
"""

if "CLAUSE_SCANNER_RE" not in content:
    # Insert it right before def tokenize
    tokenize_idx = content.find("TOKEN_REGEX = re.compile(")
    if tokenize_idx == -1:
        print("Could not find TOKEN_REGEX")
        exit(1)

    content = content[:tokenize_idx] + scanner_re_def + "\n" + content[tokenize_idx:]
    with open('sql_compare.py', 'w') as f:
        f.write(content)
    print("Injected CLAUSE_SCANNER_RE")
else:
    print("CLAUSE_SCANNER_RE already injected")

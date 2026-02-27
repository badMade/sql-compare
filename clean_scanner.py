#!/usr/bin/env python3
import sys

# Read the file
with open('sql_compare.py', 'r') as f:
    lines = f.readlines()

# We need to remove the duplicate and broken class definitions inserted around line 58.
# Based on the previous 'sed -n', we have a partial implementation from lines 58 to 150-ish.
# The original 'uppercase_outside_quotes' probably started around line 57 originally, but pushed down.

# Let's find where 'def uppercase_outside_quotes' is now.
def_line_idx = -1
for i, line in enumerate(lines):
    if "def uppercase_outside_quotes" in line:
        def_line_idx = i
        break

if def_line_idx == -1:
    print("Could not find uppercase_outside_quotes")
    sys.exit(1)

# We want to keep lines up to 'def collapse_whitespace' end (approx line 56).
# Actually, we can just look for the first occurrence of 'class _SQLScanner'.
first_scanner_idx = -1
for i, line in enumerate(lines):
    if "class _SQLScanner:" in line:
        first_scanner_idx = i
        break

if first_scanner_idx != -1 and first_scanner_idx < def_line_idx:
    # Remove everything between first scanner and def_line_idx
    # And insert the correct implementation
    del lines[first_scanner_idx:def_line_idx]

# Now insert the correct implementation
correct_scanner = """class _SQLScanner:
    \"\"\"
    Helper class to scan SQL strings while tracking quoting and parenthesis nesting state.
    \"\"\"
    def __init__(self, sql: str, start: int = 0):
        self.sql = sql
        self.n = len(sql)
        self.i = start
        self.mode = None  # None, 'single', 'double', 'bracket', 'backtick'
        self.level = 0

    def step(self) -> str:
        \"\"\"
        Consume the next character(s) and update state.
        Returns the consumed character(s) as a string.
        \"\"\"
        if self.i >= self.n:
            return ""

        ch = self.sql[self.i]

        # If we are in a quoting mode, handle it
        if self.mode == 'single':
            self.i += 1
            if ch == "'":
                if self.i < self.n and self.sql[self.i] == "'":
                    # Escaped quote ''
                    self.i += 1
                    return "''"
                else:
                    self.mode = None
                    return "'"
            return ch

        elif self.mode == 'double':
            self.i += 1
            if ch == '"':
                if self.i < self.n and self.sql[self.i] == '"':
                    # Escaped quote ""
                    self.i += 1
                    return '""'
                else:
                    self.mode = None
                    return '"'
            return ch

        elif self.mode == 'bracket':
            self.i += 1
            if ch == ']':
                self.mode = None
            return ch

        elif self.mode == 'backtick':
            self.i += 1
            if ch == '`':
                self.mode = None
            return ch

        # mode is None
        self.i += 1
        if ch == "'":
            self.mode = 'single'
        elif ch == '"':
            self.mode = 'double'
        elif ch == '[':
            self.mode = 'bracket'
        elif ch == '`':
            self.mode = 'backtick'
        elif ch == '(':
            self.level += 1
        elif ch == ')':
            self.level = max(0, self.level - 1)

        return ch

"""

lines.insert(first_scanner_idx, correct_scanner)

with open('sql_compare.py', 'w') as f:
    f.writelines(lines)

print("Fixed sql_compare.py")

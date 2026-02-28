import re

correct_code = r'''class _SQLScanner:
    """
    Helper to scan SQL text while tracking quote/paren/bracket state.
    Used to implement split_top_level, uppercase_outside_quotes, etc.
    """
    def __init__(self, sql: str):
        self.sql = sql
        self.i = 0
        self.n = len(sql)
        self.mode = None  # 'single', 'double', 'bracket', 'backtick'
        self.level = 0    # parenthesis nesting level

    def step(self) -> str:
        if self.i >= self.n:
            return ""
        ch = self.sql[self.i]

        if self.mode is None:
            if ch == "'": self.mode = 'single'
            elif ch == '"': self.mode = 'double'
            elif ch == '[': self.mode = 'bracket'
            elif ch == '`': self.mode = 'backtick'
            elif ch == '(': self.level += 1
            elif ch == ')': self.level = max(0, self.level - 1)
            self.i += 1
            return ch
        else:
            if self.mode == 'single' and ch == "'":
                if self.i + 1 < self.n and self.sql[self.i + 1] == "'":
                    self.i += 2
                    return "''"
                else:
                    self.mode = None
                    self.i += 1
                    return ch
            elif self.mode == 'double' and ch == '"':
                if self.i + 1 < self.n and self.sql[self.i + 1] == '"':
                    self.i += 2
                    return '""'
                else:
                    self.mode = None
                    self.i += 1
                    return ch
            elif self.mode == 'bracket' and ch == ']':
                self.mode = None
                self.i += 1
                return ch
            elif self.mode == 'backtick' and ch == '`':
                self.mode = None
                self.i += 1
                return ch

            self.i += 1
            return ch
'''

with open("sql_compare.py", "r") as f:
    content = f.read()

start_marker = "# =============================\n# Normalization & Utilities\n# ============================="
idx = content.find(start_marker)
if idx != -1:
    insert_pos = idx + len(start_marker)
    if "class _SQLScanner:" not in content:
        new_content = content[:insert_pos] + "\n\n" + correct_code + "\n" + content[insert_pos:]
        with open("sql_compare.py", "w") as f:
            f.write(new_content)
        print("Inserted _SQLScanner")

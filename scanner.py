
class _SQLScanner:
    def __init__(self, sql: str, start: int = 0):
        self.sql = sql
        self.n = len(sql)
        self.i = start
        self.mode = None  # None, 'single', 'double', 'bracket', 'backtick'
        self.level = 0

    def step(self) -> str:
        if self.i >= self.n:
            return ""

        ch = self.sql[self.i]
        self.i += 1

        # If we were already in a mode, handle exit or escape
        if self.mode == 'single':
            if ch == "'":
                if self.i < self.n and self.sql[self.i] == "'":
                    self.i += 1
                    return "''"
                self.mode = None
            return ch

        elif self.mode == 'double':
            if ch == '"':
                if self.i < self.n and self.sql[self.i] == '"':
                    self.i += 1
                    return '""'
                self.mode = None
            return ch

        elif self.mode == 'bracket':
            if ch == ']':
                self.mode = None
            return ch

        elif self.mode == 'backtick':
            if ch == '`':
                self.mode = None
            return ch

        # mode is None
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

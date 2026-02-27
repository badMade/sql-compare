class _SQLScanner:
    """
    Helper class to scan SQL strings while tracking quoting and parenthesis nesting state.
    """
    def __init__(self, sql: str, start: int = 0):
        self.sql = sql
        self.n = len(sql)
        self.i = start
        self.mode = None  # None, 'single', 'double', 'bracket', 'backtick'
        self.level = 0

    def step(self) -> str:
        """
        Consume the next character(s) and update state.
        Returns the consumed character(s) as a string.
        """
        if self.i >= self.n:
            return ""

        ch = self.sql[self.i]

        if self.mode is None:
            self.i += 1
            if ch == "'":
                self.mode = 'single'
                return ch
            elif ch == '"':
                self.mode = 'double'
                return ch
            elif ch == '[':
                self.mode = 'bracket'
                return ch
            elif ch == '`':
                self.mode = 'backtick'
                return ch
            elif ch == '(':
                self.level += 1
                return ch
            elif ch == ')':
                self.level = max(0, self.level - 1)
                return ch
            else:
                return ch

        elif self.mode == 'single':
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

        return ""

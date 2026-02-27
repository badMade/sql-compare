import re

# Snippets from sql_compare.py for analysis

def _parse_from_clause_body(body: str):
    i = 0; n = len(body)
    mode = None; level = 0
    tokens = []
    # ... (logic follows)

def split_top_level(s: str, sep: str) -> list:
    parts, buf = [], []
    level = 0; mode = None; i = 0
    while i < len(s):
        ch = s[i]
        # ... (similar logic follows)

def top_level_find_kw(sql: str, kw: str, start: int = 0):
    i = start; mode = None; level = 0
    while i < len(sql):
        ch = sql[i]
        # ... (similar logic follows)

print("Identified 3 functions with duplicate state machine logic:")
print("1. _parse_from_clause_body")
print("2. split_top_level")
print("3. top_level_find_kw")

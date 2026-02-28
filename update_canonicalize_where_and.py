import re

with open("sql_compare.py", "r", encoding="utf-8") as f:
    content = f.read()

old_func = """def canonicalize_where_and(sql: str) -> str:
    s = collapse_whitespace(sql)
    where_i = top_level_find_kw(s, "WHERE", 0)
    if where_i == -1: return s
    end_i = clause_end_index(s, where_i + 5)
    body = s[where_i + 5:end_i].strip()
    terms = split_top_level(body, " AND ")
    if len(terms) > 1:
        terms_sorted = sorted([collapse_whitespace(t) for t in terms], key=lambda z: z.upper())
        new_body = " AND ".join(terms_sorted)
        s = s[:where_i + 5] + " " + new_body + " " + s[end_i:]
    return collapse_whitespace(s)"""

new_func = """def canonicalize_where_and(sql: str) -> str:
    s = collapse_whitespace(sql)
    where_i = top_level_find_kw(s, "WHERE", 0)
    if where_i == -1: return s
    end_i = clause_end_index(s, where_i + 5)
    body = s[where_i + 5:end_i].strip()

    or_terms = split_top_level(body, " OR ")
    new_or_terms = []

    for or_term in or_terms:
        and_terms = split_top_level(or_term, " AND ")
        if len(and_terms) > 1:
            and_terms_sorted = sorted([collapse_whitespace(t) for t in and_terms], key=lambda z: z.upper())
            new_or_terms.append(" AND ".join(and_terms_sorted))
        else:
            new_or_terms.append(collapse_whitespace(or_term))

    if len(new_or_terms) > 1:
        new_or_terms_sorted = sorted(new_or_terms, key=lambda z: z.upper())
        new_body = " OR ".join(new_or_terms_sorted)
    else:
        new_body = new_or_terms[0]

    s = s[:where_i + 5] + " " + new_body + " " + s[end_i:]
    return collapse_whitespace(s)"""

content = content.replace(old_func, new_func)

with open("sql_compare.py", "w", encoding="utf-8") as f:
    f.write(content)

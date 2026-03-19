🔒 Sentinel: [Medium] Fix SQL Parsing Evasion via Comments

🎯 **What:** The `strip_sql_comments` function in `sql_compare.py` was vulnerable to SQL parsing evasion. The original implementation used naive global `re.sub` regexes to remove `--` and `/* ... */` comments. This did not respect string literal boundaries (`'`, `"`) or identifier boundaries (`[]`, `` ` ``).

⚠️ **Risk:** An attacker or malicious input could craft a string literal containing comment characters (e.g., `SELECT 'This is -- not a comment'`). This would trick the normalizer into corrupting the query, potentially hiding malicious SQL or causing false positives/negatives in the comparison engine.

🛡️ **Solution:** The solution replaces the naive `re.sub` approach with a robust, tokenization-style regular expression (`SQL_COMMENT_OR_STRING_REGEX`). The new parser iterates through matches for strings, bracketed/backticked identifiers, and comments. It only replaces tokens that actually start with `--` or `/*`, while safely preserving string contents and unstructured SQL text around them.

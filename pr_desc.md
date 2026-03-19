🎯 **What:** The `split_top_level` parsing utility in `sql_compare.py` was missing test coverage. This function is critical for correctly parsing SQL strings without splitting separators (like `,` or `AND`) that are inside string literals, identifiers, or nested parentheses.

📊 **Coverage:** The new `TestSplitTopLevel` class comprehensively tests:
- Basic splitting functionality
- Ignoring separators inside single and double quotes
- Ignoring separators inside brackets `[]` and backticks ``` `` ```
- Ignoring separators inside nested parentheses `()`
- Empty string and separator-only handling
- Handling of consecutive separators (e.g., `A,,B`)
- Graceful handling of unbalanced quotes/brackets/parentheses
- Case-sensitive separator matching (documenting current baseline behavior)

✨ **Result:** Enhanced test coverage that establishes a solid regression baseline for `split_top_level`, improving the overall reliability of the SQL parsing mechanisms and enabling confident future refactoring.
🎯 **What:** The `canonicalize_select_list` function in `sql_compare.py` was completely untested. This function is responsible for alphabetizing `SELECT` statement items to facilitate deterministic comparison. This PR introduces a comprehensive test suite for it, establishing a reliable baseline.

📊 **Coverage:** The new `TestCanonicalizeSelectList` class in `tests/test_sql_compare.py` covers the following scenarios:
*   Happy path alphabetical sorting.
*   Single item selects (no changes expected).
*   Case-insensitive sorting.
*   Statements missing `SELECT` or `FROM` keywords.
*   Nested commas inside strings, functions (`coalesce()`), and subqueries.
*   Handling and collapse of extra whitespace.
*   Aliases (sorting them along with their columns as a single unit).
*   *Edge Case Baseline:* The tests explicitly document the current sub-optimal handling of the `DISTINCT` keyword (where `DISTINCT b, a` gets sorted as `a, DISTINCT b`). This complies with TDD baseline documentation principles prior to any future refactoring.

✨ **Result:** Increased test coverage and reliability for SQL string canonicalization. The test suite correctly identifies the current behaviors and ensures any future changes to `canonicalize_select_list` won't cause unexpected regressions in SQL comparison logic.

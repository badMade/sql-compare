## 2024-03-18 - [Optimize string concatenation in loop]
**Learning:** Using `base = (base + " " + text).strip()` inside a `while` loop operates in O(N^2) time due to repeated string memory allocation and data copying on each iteration. For `_extract_base_table` in `sql_compare.py`, 50k tokens took 4.7s.
**Action:** Replaced the O(N^2) repeated string concatenation loop with an O(N) list-append pattern (`parts.append(text)`) followed by a final `" ".join(parts)`, handling `.strip()` and `.rstrip()` correctly to preserve the exact same whitespace stripping behavior as the previous loop execution. This resulted in a speedup to 0.012s for 50k tokens.

## 2026-03-30 - [Python string splitting performance vs Regex]
**Learning:** Python's built-in `.split()` combined with `' '.join()` is significantly faster (~5x) than using `re.sub(r'\s+', ' ', s).strip()` for collapsing consecutive whitespace. The C implementation of `split()` natively handles consecutive whitespace collapsing without the overhead of regex compilation and execution.
**Action:** When the goal is strictly collapsing all whitespace into single spaces and trimming, prefer `' '.join(s.split())` over regex in heavily called functions.

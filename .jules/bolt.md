## 2024-05-20 - [O(N^2) String Slicing in Parsing Loops]
**Learning:** Using `re.match(pattern, string[i:])` inside a `while` loop that advances character by character causes O(N^2) memory and time overhead due to continuous string slicing in Python.
**Action:** Use pre-compiled regexes and the `pos` argument like `pattern.match(string, i)` to evaluate word boundaries and regexes efficiently without copying the string. Additionally, note that `m.end()` from `pattern.match(string, i)` returns the absolute index, so index advancement should be `i = m.end()` rather than `i += m.end()`.

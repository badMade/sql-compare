## 2024-05-19 - Fast String Traversal
**Learning:** Python's `while i < len(s): ch = s[i]` character-by-character string traversal loops are significant performance bottlenecks for string parsing operations (like identifying quotes, comments, or parentheses).
**Action:** When profiling shows these loops are hotspots, consider replacing them with `re.finditer` using compiled regexes to offload the scanning loop to C, provided this preserves correctness and keeps the parsing logic maintainable.

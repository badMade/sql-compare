## 2024-03-19 - Eliminate redundant whitespace collapse passes
**Learning:** `collapse_whitespace` operations are expensive when chained. When composing multiple string canonicalization functions (like SELECT, WHERE, and JOIN processing), extracting internal functions (e.g., `_canonicalize_...`) that assume pre-collapsed input prevents redundant regex evaluations and string allocations.
**Action:** Refactored `canonicalize_common` to do a single `collapse_whitespace` pass and chain internal canonicalization functions, yielding a ~40% performance boost.

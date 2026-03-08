---
applyTo:
  "**/*"
---

# Bugs & Refactors

## Bug Workflow (Minimal, Test-Proven Changes)
1) **Scan**: detect logic errors, edge cases, behavior mismatches  
2) **Report**: file/line, description, impact, minimal fix plan **before editing**  
3) **Fix**: apply the **smallest clean fix**; avoid unrelated refactors  
4) **Verify**: add failing test pre-fix; confirm pass post-fix; run full suite  
5) **Output**: Bug report, Fix summary, Verification log

> Constraints: prioritize correctness, reproducibility, determinism; minimize churn; document reasoning only when essential.

## Refactoring Policy (Controlled)
- **Do not mix** refactors with feature changes.
- Preserve **external behavior**; list files touched.
- Provide **before/after** complexity notes (function counts, complexity deltas).
- Large refactors: add **snapshot tests**; expand runbooks as needed.

---
applyTo:
  "**/*.{py,toml,txt}"
---

# Python Standards (Clean Code + Complexity Constraints)

## Clean Code
- Prefer clarity, readability, minimalism, modularity.
- Intention-revealing names; remove duplication and dead code.
- **Single responsibility** functions/classes; testable units.
- No hidden side effects or unnecessary dependencies.
- Clear exception handling; **fail fast**; clean up resources.
- Consistent formatting and module boundaries.
- Comments explain **why**, not what.

## Complexity
- Keep cyclomatic complexity within team-defined cap; avoid nesting > 3 levels.
- Justify recursion/metaprogramming/reflection with explicit trade-offs.
- Run a **simplification pass** on AI-generated code before review.

## Python-Specific
- Use typing and docstrings (Google or NumPy style).
- Deterministic I/O and seeded randomness for tests.
```
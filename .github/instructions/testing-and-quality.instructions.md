---
applyTo:
  "**/{*test*.*,tests/**,.github/workflows/*.yml,pytest.ini,jest.config.*,coverage*}"
---

# Testing & Quality Gates (Tool-Agnostic)

- **Bug fixes**: add a failing test *before* the fix (TDD for defects).
- Cover **edge cases**, **failure modes**, and **security boundaries**.
- Maintain team-defined **coverage threshold**; monitor trend.
- Run static analysis, formatting, linting, and type checks in CI.
- Consider mutation-style checks where feasible.
- All gates must pass; overrides require tech-lead approval + rationale.

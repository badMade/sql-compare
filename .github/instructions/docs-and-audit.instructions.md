---
applyTo:
  "**/*.{md,rst,txt}"
---

# Documentation & Audit

## Audit Scope
- Inspect source, scripts, configs; locate `README.md`, `NOTES.txt`, `requirements.txt`/`pyproject.toml`, `*.md`, `*.rst`, and docstrings.
- Identify **missing, outdated, or TODO** documentation.

## README Must Include
- Overview (purpose, functionality, rationale)
- Install for **local/CI/container/prod-like**
- Usage examples (CLI and API)
- File/module structure overview
- Troubleshooting and contribution guide

## Docstrings
- **Styles**: Google or NumPy
- **Required**: public classes, functions, modules
- **Content**: args, returns, side-effects, usage notes
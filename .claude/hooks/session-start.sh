#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Verify Python 3 is available
if ! command -v python3 &> /dev/null; then
  echo "ERROR: python3 is not available" >&2
  exit 1
fi

# Install flake8 for linting (idempotent — pip skips if already installed)
pip install --quiet flake8

# Smoke test: verify sql_compare.py can parse and compare
python3 "$CLAUDE_PROJECT_DIR/sql_compare.py" \
  --strings "SELECT a FROM t" "SELECT a FROM t" --mode exact

echo "Session start hook completed successfully"

#!/usr/bin/env bash
# cleanup_redundant_prs.sh
#
# Closes redundant open PRs in badMade/sql-compare.
# Many PRs address the same issue (e.g., multiple XSS fixes, multiple
# empty-state UX PRs, multiple performance optimizations for the same
# function). This script keeps the latest PR in each group and closes
# the duplicates.
#
# Requires: gh CLI authenticated with repo access
#
# Usage: bash cleanup_redundant_prs.sh [--dry-run]

set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "=== DRY RUN MODE ==="
fi

# ── Redundant PR groups ──────────────────────────────────────────────
# Each group: first line = kept PR, remaining lines = redundant PRs to close

# Sentinel XSS fixes — keep #138
XSS_CLOSE=(136 133 129 126 124 121)

# Sentinel DoS / unbounded stdin — keep #179
DOS_CLOSE=(178 175 166)

# Palette empty-state UX — keep #180
PALETTE_CLOSE=(177 176 168 157 139 137 132 131 128 125 122)

# Bolt optimize top_level_find_kw — keep #134
BOLT_CLOSE=(130 127 123 120)

ALL_CLOSE=("${XSS_CLOSE[@]}" "${DOS_CLOSE[@]}" "${PALETTE_CLOSE[@]}" "${BOLT_CLOSE[@]}")

echo "Will close ${#ALL_CLOSE[@]} redundant PRs:"
echo ""
echo "Sentinel XSS (keep #138):          close ${XSS_CLOSE[*]}"
echo "Sentinel DoS (keep #179):          close ${DOS_CLOSE[*]}"
echo "Palette empty-state (keep #180):   close ${PALETTE_CLOSE[*]}"
echo "Bolt optimize (keep #134):         close ${BOLT_CLOSE[*]}"
echo ""

closed=0
failed=0

for pr in "${ALL_CLOSE[@]}"; do
  if $DRY_RUN; then
    echo "[dry-run] Would close PR #${pr}"
  else
    if gh pr close "$pr" --repo badMade/sql-compare \
         --comment "Closing as redundant — a newer PR addresses the same issue."; then
      echo "✓ Closed PR #${pr}"
      ((closed+=1))
    else
      echo "✗ Failed to close PR #${pr}"
      ((failed+=1))
    fi
  fi
done

echo ""
if $DRY_RUN; then
  echo "Dry run complete. ${#ALL_CLOSE[@]} PRs would be closed."
else
  echo "Done. Closed: ${closed}, Failed: ${failed}"
fi

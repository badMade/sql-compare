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
# Usage: bash cleanup_redundant_prs.sh [--dry-run] [--yes]

set -euo pipefail

DRY_RUN=false
YES=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      echo "=== DRY RUN MODE ==="
      ;;
    --yes)
      YES=true
      ;;
    -h|--help)
      echo "Usage: bash cleanup_redundant_prs.sh [--dry-run] [--yes]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: bash cleanup_redundant_prs.sh [--dry-run] [--yes]" >&2
      exit 1
      ;;
  esac
  shift
done

if ! $DRY_RUN && ! $YES; then
  echo "Refusing to close PRs without explicit confirmation."
  echo "Re-run with --dry-run to preview, or with --yes to proceed."
  exit 1
fi

# ── Redundant PR groups ──────────────────────────────────────────────
# Each group lists redundant PR numbers to close; the kept PR is noted in the comment above.

# Sentinel XSS fixes — keep #138
XSS_CLOSE=(136 133 129 126 124 121)

# Sentinel DoS / unbounded stdin — keep #179
DOS_CLOSE=(178 175 166)

# Palette empty-state UX — keep #180
PALETTE_CLOSE=(177 176 168 157 139 137 132 131 128 125 122)

# Bolt optimize top_level_find_kw — keep #134
BOLT_CLOSE=(130 127 123 120)

# Bolt optimize other functions (uppercase_outside_quotes, tokenize) — keep #134
BOLT_OTHER_CLOSE=(174 173 164)

ALL_CLOSE=("${XSS_CLOSE[@]}" "${DOS_CLOSE[@]}" "${PALETTE_CLOSE[@]}" "${BOLT_CLOSE[@]}" "${BOLT_OTHER_CLOSE[@]}")

echo "Will close ${#ALL_CLOSE[@]} redundant PRs:"
echo ""
echo "Sentinel XSS (keep #138):          close ${XSS_CLOSE[*]}"
echo "Sentinel DoS (keep #179):          close ${DOS_CLOSE[*]}"
echo "Palette empty-state (keep #180):   close ${PALETTE_CLOSE[*]}"
echo "Bolt optimize (keep #134):         close ${BOLT_CLOSE[*]}"
echo "Bolt other perf (keep #134):       close ${BOLT_OTHER_CLOSE[*]}"
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

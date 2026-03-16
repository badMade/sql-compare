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

ALL_CLOSE=("${XSS_CLOSE[@]}" "${DOS_CLOSE[@]}" "${PALETTE_CLOSE[@]}" "${BOLT_CLOSE[@]}")

# Define kept PRs and specific comments for each group
KEPT_PR_XSS=138
COMMENT_XSS="Closing as redundant in favor of #${KEPT_PR_XSS}, which addresses the same issue."

KEPT_PR_DOS=179
COMMENT_DOS="Closing as redundant in favor of #${KEPT_PR_DOS}, which addresses the same issue."

KEPT_PR_PALETTE=180
COMMENT_PALETTE="Closing as redundant in favor of #${KEPT_PR_PALETTE}, which addresses the same issue."

KEPT_PR_BOLT=134
COMMENT_BOLT="Closing as redundant in favor of #${KEPT_PR_BOLT}, which addresses the same issue."

echo "Will close ${#ALL_CLOSE[@]} redundant PRs:"
echo ""
echo "Sentinel XSS (keep #138):          close ${XSS_CLOSE[*]}"
echo "Sentinel DoS (keep #179):          close ${DOS_CLOSE[*]}"
echo "Palette empty-state (keep #180):   close ${PALETTE_CLOSE[*]}"
echo "Bolt optimize (keep #134):         close ${BOLT_CLOSE[*]}"
echo ""

closed=0
failed=0

# Process Sentinel XSS fixes
for pr in "${XSS_CLOSE[@]}"; do
  if $DRY_RUN; then
    echo "[dry-run] Would close PR #${pr} (XSS, kept #${KEPT_PR_XSS})"
  else
    if gh pr close "$pr" --repo badMade/sql-compare \
         --comment "$COMMENT_XSS"; then
      echo "✓ Closed PR #${pr} (XSS, kept #${KEPT_PR_XSS})"
      ((closed+=1))
    else
      echo "✗ Failed to close PR #${pr} (XSS, kept #${KEPT_PR_XSS})"
      ((failed+=1))
    fi
  fi
done

# Process Sentinel DoS / unbounded stdin fixes
for pr in "${DOS_CLOSE[@]}"; do
  if $DRY_RUN; then
    echo "[dry-run] Would close PR #${pr} (DoS, kept #${KEPT_PR_DOS})"
  else
    if gh pr close "$pr" --repo badMade/sql-compare \
         --comment "$COMMENT_DOS"; then
      echo "✓ Closed PR #${pr} (DoS, kept #${KEPT_PR_DOS})"
      ((closed+=1))
    else
      echo "✗ Failed to close PR #${pr} (DoS, kept #${KEPT_PR_DOS})"
      ((failed+=1))
    fi
  fi
done

# Process Palette empty-state UX fixes
for pr in "${PALETTE_CLOSE[@]}"; do
  if $DRY_RUN; then
    echo "[dry-run] Would close PR #${pr} (Palette, kept #${KEPT_PR_PALETTE})"
  else
    if gh pr close "$pr" --repo badMade/sql-compare \
         --comment "$COMMENT_PALETTE"; then
      echo "✓ Closed PR #${pr} (Palette, kept #${KEPT_PR_PALETTE})"
      ((closed+=1))
    else
      echo "✗ Failed to close PR #${pr} (Palette, kept #${KEPT_PR_PALETTE})"
      ((failed+=1))
    fi
  fi
done

# Process Bolt optimize top_level_find_kw fixes
for pr in "${BOLT_CLOSE[@]}"; do
  if $DRY_RUN; then
    echo "[dry-run] Would close PR #${pr} (Bolt, kept #${KEPT_PR_BOLT})"
  else
    if gh pr close "$pr" --repo badMade/sql-compare \
         --comment "$COMMENT_BOLT"; then
      echo "✓ Closed PR #${pr} (Bolt, kept #${KEPT_PR_BOLT})"
      ((closed+=1))
    else
      echo "✗ Failed to close PR #${pr} (Bolt, kept #${KEPT_PR_BOLT})"
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

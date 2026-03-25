# GitHub Actions Workflows Documentation

## Overview

This repository uses several GitHub Actions workflows to automate code review and other tasks. This document explains when these workflows run and why they might be skipped.

## AI Review Workflows

### Codex Review (`codex.yml`)

Uses OpenAI GPT-4 to review pull request changes.

**Triggers:**
- Pull request events: `opened`, `labeled`, `synchronize` (when new commits are pushed)
- Issue comments containing `@codex`
- Pull request review comments containing `@codex`

### Jules Review (`jules.yml`)

Uses Google Gemini to review pull request changes.

**Triggers:**
- Pull request events: `opened`, `labeled`, `synchronize` (when new commits are pushed)
- Issue comments containing `@jules`
- Pull request review comments containing `@jules`

## Why Workflows Are Skipped

Both Codex Review and Jules Review workflows will be **skipped** if certain conditions are not met:

### 1. Missing Required Label

**Most Common Reason for Skipped Checks**

Both workflows require the `safe-for-ai-review` label to be present on the pull request. This is a security measure to ensure that only explicitly marked PRs are reviewed by AI.

**Solution:** Add the `safe-for-ai-review` label to your PR.

### 2. Fork/External Pull Requests

Workflows only run on pull requests from branches within the same repository (`badMade/sql-compare`), not from forks.

**Why:** This prevents exposure of repository secrets (API keys) to external contributors.

**Condition:** `github.event.pull_request.head.repo.full_name == github.repository`

### 3. Unauthorized Mentions

When triggered by comments (`@codex` or `@jules`), the comment author must be a repository member, owner, or collaborator.

**Condition:** `github.event.comment.author_association` must be `MEMBER`, `OWNER`, or `COLLABORATOR`

### 4. Missing API Keys

- Codex Review requires `OPENAI_API_KEY` secret
- Jules Review requires `GOOGLE_API_KEY` secret

If these secrets are not configured, the workflows will fail (but not skip).

## Workflow Trigger Matrix

| Trigger Type | Event | Required Conditions |
|-------------|-------|-------------------|
| **Pull Request** | `opened`, `labeled`, `synchronize` | Internal PR + `safe-for-ai-review` label |
| **Issue Comment** | Comment with `@codex` or `@jules` | Author is MEMBER/OWNER/COLLABORATOR + PR has `safe-for-ai-review` label + Comment is on a PR |
| **PR Review Comment** | Review comment with `@codex` or `@jules` | Internal PR + Author is MEMBER/OWNER/COLLABORATOR + PR has `safe-for-ai-review` label |

## How to Enable Reviews for Your PR

1. Ensure your PR is from a branch in this repository (not a fork)
2. Add the `safe-for-ai-review` label to your PR
3. Either:
   - Wait for automatic review when PR is opened/updated, OR
   - Manually trigger by commenting `@codex` or `@jules`

## Testing Workflows

Tests for workflow configurations are located in `tests/test_workflows.py`:

- `test_codex_and_jules_have_same_trigger_events` - Ensures both workflows have identical trigger events
- `test_review_workflows_require_safe_for_ai_review_label` - Verifies label requirement is enforced

Run tests with:
```bash
python -m unittest discover -s tests
```

## Related Files

- `.github/workflows/codex.yml` - Codex Review workflow configuration
- `.github/workflows/jules.yml` - Jules Review workflow configuration
- `.github/actions/review-utils.js` - Shared utilities for review workflows
- `tests/test_workflows.py` - Workflow configuration tests

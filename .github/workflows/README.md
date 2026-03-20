# GitHub Actions Workflows

This directory contains automated workflows for the sql-compare repository.

## AI Code Review Workflows

Three AI-powered code review workflows are available to automatically review pull requests:

### 1. Jules Review (Google Gemini)

**File:** `jules.yml`

**Triggers:**
- Automatically on new PRs from the same repository
- On-demand by commenting `@jules` in a PR comment or review comment

**Prerequisites:**
- `GOOGLE_API_KEY` secret must be configured in repository settings
- The API key must have access to Google's Generative AI API (Gemini)

**Configuration:**
1. Go to repository Settings → Secrets and variables → Actions
2. Add a new secret named `GOOGLE_API_KEY`
3. Obtain an API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
4. Ensure the key has appropriate permissions for the Gemini API

**Security Notes:**
- The API key is validated before use without exposing the secret value
- All API calls are logged (status codes only, not responses)
- Failed API calls include truncated error messages (first 500 chars)

### 2. Codex Review (OpenAI GPT-4)

**File:** `codex.yml`

**Triggers:**
- Automatically on new PRs from the same repository
- On-demand by commenting `@codex` in a PR comment or review comment

**Prerequisites:**
- `OPENAI_API_KEY` secret must be configured in repository settings
- The API key must have access to OpenAI's GPT-4 models

**Configuration:**
1. Go to repository Settings → Secrets and variables → Actions
2. Add a new secret named `OPENAI_API_KEY`
3. Obtain an API key from [OpenAI Platform](https://platform.openai.com/api-keys)
4. Ensure the key has access to the `gpt-4o` model

**Security Notes:**
- The API key is validated before use without exposing the secret value
- All API calls are logged (status codes only, not responses)
- Failed API calls include truncated error messages (first 500 chars)

### 3. Claude Review (Anthropic)

**File:** `claude.yml`

**Triggers:**
- Automatically on new PRs and synchronizations
- On issue comments, PR review comments, and issue assignments

**Prerequisites:**
- `ANTHROPIC_API_KEY` secret must be configured in repository settings
- Uses the official `anthropics/claude-code-action@v1` action

**Configuration:**
1. Go to repository Settings → Secrets and variables → Actions
2. Add a new secret named `ANTHROPIC_API_KEY`
3. Obtain an API key from [Anthropic Console](https://console.anthropic.com/)

## Common Features

### Pagination Support
Both Jules and Codex workflows support large PRs with:
- Up to 10 pages of files (100 files per page)
- Maximum of 1000 files per PR review
- Graceful handling of pagination errors

### Error Handling
All workflows include:
- Comprehensive logging using GitHub Actions `core` API
- Informative error messages without exposing secrets
- Graceful skipping when API keys are not configured
- Proper handling of non-PR issue comments

### Logging
Workflows use GitHub Actions native logging:
- `core.info()` for informational messages
- `core.warning()` for non-fatal issues
- `core.error()` for errors
- `core.setFailed()` for workflow failures

### Security Best Practices
- API keys are stored as secrets and never logged
- All API calls validate keys before use
- Error responses are truncated to prevent secret leakage
- Only PRs from the same repository are automatically reviewed

## Other Workflows

### Auto-assign Reviewers

**File:** `auto-assign-reviewers.yml`

Automatically assigns team reviewers to new pull requests.

### Cleanup Redundant PRs

**File:** `cleanup-redundant-prs.yml`

Automatically closes redundant pull requests and posts explanatory comments.

### Copilot Setup Steps

**File:** `copilot-setup-steps.yml`

Reusable workflow for setting up Copilot agent configurations.

## Troubleshooting

### Workflow Not Running

1. Check that the triggering event matches the workflow configuration
2. Verify the PR is from the same repository (not a fork)
3. Ensure required API keys are configured as secrets

### API Key Validation Fails

1. Go to repository Settings → Secrets and variables → Actions
2. Verify the secret name matches exactly (e.g., `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
3. Ensure the API key is valid and has necessary permissions

### Reviews Not Appearing

1. Check the Actions tab for workflow run logs
2. Look for error messages in the "Review with [AI]" step
3. Verify the API key has sufficient quota/credits
4. Check that the PR has actual file changes (not just merge commits)

### Large PR Issues

For PRs with more than 1000 files:
- Only the first 1000 files will be reviewed
- Consider breaking the PR into smaller chunks
- Manual review may be more appropriate

## Development

### Testing Workflows

To test workflow changes:
1. Create a test branch
2. Modify the workflow file
3. Open a PR to trigger the workflow
4. Check the Actions tab for execution logs

### Adding New Workflows

When adding new workflows:
1. Follow the existing patterns for error handling
2. Use `core.info()`, `core.warning()`, and `core.error()` for logging
3. Validate secrets before use without exposing values
4. Add documentation to this README
5. Test thoroughly with edge cases

## Contributing

When modifying AI review workflows:
- Maintain security best practices for API key handling
- Preserve pagination support for large PRs
- Use GitHub Actions native logging functions
- Add inline comments explaining non-obvious logic
- Update this README with any configuration changes

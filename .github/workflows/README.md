# AI Review Workflows

This repo includes two AI-assisted review workflows:

- `codex.yml` uses OpenAI (Codex).
- `jules.yml` uses Google Gemini (Jules).

## Prerequisites

- Add the appropriate API key as a repository secret:
  - `OPENAI_API_KEY` for `codex.yml`
  - `GOOGLE_API_KEY` for `jules.yml`
- Label the pull request with `safe-for-ai-review` to allow automatic runs on PR open. Issue/PR comments that mention the bot handle (`@codex` or `@jules`) also trigger reviews when keys are present.
- Checkout steps use `fetch-depth: 0` to ensure complete history for accurate diffs and label evaluation.

## Notes

- Workflows fetch PR diffs via the GitHub REST API with pagination and limit logging to statuses (no secret values).
- Failures from the external APIs are surfaced with status codes and request URLs for easier debugging.

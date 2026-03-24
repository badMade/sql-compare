'use strict';

const MAX_PAGES = 10;

/**
 * Extract the PR number from a webhook payload.
 * Works for pull_request, issue_comment, and pull_request_review_comment events.
 */
function parsePrNumber(payload) {
  const prNumber = payload.pull_request?.number || payload.issue?.number;
  if (!prNumber) {
    throw new Error('Could not determine PR number from payload');
  }
  return prNumber;
}

/**
 * Convert a PR number from an environment variable string to a validated number.
 */
function normalizePrNumber(value) {
  const prNumber = Number(value);
  if (!prNumber || !Number.isFinite(prNumber)) {
    throw new Error(`Invalid PR number: ${value}`);
  }
  return prNumber;
}

/**
 * Fetch all changed files for a PR with pagination, capped at MAX_PAGES.
 * Also verifies that issue_comment events come from internal PRs (not forks)
 * to prevent leaking repository secrets.
 */
async function fetchPrFilesWithPagination(github, context, prNumber, core) {
  // For issue_comment events the job-level `if` cannot access head.repo.full_name,
  // so verify at runtime to prevent fork PRs from triggering reviews with repo secrets.
  if (context.eventName === 'issue_comment') {
    const { data: pr } = await github.rest.pulls.get({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber,
    });
    const baseRepo = `${context.repo.owner}/${context.repo.repo}`;
    if (pr.head.repo.full_name !== baseRepo) {
      core.info('PR is from a fork; skipping review to avoid exposing repo secrets.');
      return [];
    }
  }

  let files = [];
  let page = 1;
  while (page <= MAX_PAGES) {
    const { data: pageFiles } = await github.rest.pulls.listFiles({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber,
      per_page: 100,
      page,
    });
    files = files.concat(pageFiles);
    if (pageFiles.length < 100) break;
    page++;
  }
  if (page > MAX_PAGES) {
    throw new Error(
      `PR diff exceeds the ${MAX_PAGES}-page limit (${MAX_PAGES * 100} files); ` +
      'aborting to avoid secondary rate limits.'
    );
  }
  return files;
}

/**
 * Build a unified diff string from an array of PR file objects.
 */
function buildDiffString(files) {
  return files
    .map((f) => `--- ${f.filename}\n+++ ${f.filename}\n${f.patch || '(binary)'}`)
    .join('\n\n');
}

/**
 * Retry a fetch call with exponential-ish backoff.
 * @param {Function} fn - A function that returns a fetch Promise.
 * @param {Object} opts - { retries: number, delayMs: number }
 */
async function fetchWithRetry(fn, { retries = 2, delayMs = 2000 } = {}) {
  let lastError;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, delayMs * (attempt + 1)));
      }
    }
  }
  throw lastError;
}

/**
 * Check whether a fetch Response has a JSON content-type.
 */
function isJsonResponse(response) {
  const ct = response?.headers?.get?.('content-type') || '';
  return ct.includes('application/json');
}

/**
 * Redact potential secrets (API keys, bearer tokens) from error text
 * to prevent accidental exposure in workflow logs.
 */
function sanitizeSecrets(text) {
  return text
    .replace(/key=[^&\s]+/g, 'key=[REDACTED]')
    .replace(/Authorization:\s*Bearer\s+[^\s&]+/gi, 'Authorization: Bearer [REDACTED]')
    .replace(/x-goog-api-key:\s*[^\s&]+/gi, 'x-goog-api-key: [REDACTED]');
}

/**
 * Safely read the body text of a fetch Response, returning a fallback on failure.
 * Automatically sanitizes secrets from the response text.
 */
async function safeReadBody(response) {
  try {
    const text = await response.text();
    return sanitizeSecrets(text);
  } catch {
    return '(unable to read response body)';
  }
}

/**
 * Extract a safe error message string from an unknown error value.
 */
function safeErrorMessage(error) {
  if (error && typeof error.message === 'string') return error.message;
  return String(error);
}

module.exports = {
  buildDiffString,
  fetchPrFilesWithPagination,
  fetchWithRetry,
  isJsonResponse,
  normalizePrNumber,
  parsePrNumber,
  safeErrorMessage,
  safeReadBody,
  sanitizeSecrets,
};

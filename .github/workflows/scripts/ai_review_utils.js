'use strict';

/**
 * Shared helpers for AI review workflows.
 */

/**
 * Returns a sanitized, human-readable error message without exposing internal details.
 * @param {unknown} error
 * @returns {string}
 */
function sanitizeError(error) {
  if (error && typeof error.message === 'string') {
    return error.message.trim();
  }
  if (typeof error === 'string') {
    return error.trim();
  }
  return 'Unexpected error';
}

/**
 * Parse PR number from the event payload and ensure it is an integer.
 * @param {import('@actions/github').Context} context
 * @returns {number}
 */
function parsePrNumber(context) {
  const raw = context.payload.pull_request?.number ?? context.payload.issue?.number;
  const prNumber = Number(raw);
  if (!Number.isInteger(prNumber)) {
    throw new Error('Unable to determine pull request number.');
  }
  return prNumber;
}

/**
 * Ensure we only process events from the same repository (avoid fork secrets exposure).
 * @param {import('@actions/github').Context} context
 * @returns {boolean}
 */
function isSameRepository(context) {
  const headRepo = context.payload.pull_request?.head?.repo?.full_name;
  const currentRepo = `${context.repo.owner}/${context.repo.repo}`;
  return !headRepo || headRepo === currentRepo;
}

/**
 * Build the unified diff string for a PR.
 * @param {import('@actions/github').Octokit} github
 * @param {import('@actions/github').Context} context
 * @param {number} prNumber
 * @returns {Promise<string>}
 */
async function collectPrDiff(github, context, prNumber) {
  const files = await github.paginate(github.rest.pulls.listFiles, {
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: prNumber,
    per_page: 100,
  });

  return files
    .map((file) => `--- ${file.filename}\n+++ ${file.filename}\n${file.patch || '(binary)'}`)
    .join('\n\n');
}

/**
 * Resolve PR number, ensure event is valid, and set outputs for downstream steps.
 * @param {{ core: import('@actions/core'), github: import('@actions/github').Octokit, context: import('@actions/github').Context }} params
 */
async function resolvePrContext({ core, github, context }) {
  try {
    if (context.eventName === 'issue_comment' && !context.payload.issue.pull_request) {
      core.info('Issue comment not on a pull request; skipping.');
      core.setOutput('skip', 'true');
      return;
    }

    if (!isSameRepository(context)) {
      core.info('Pull request originates from a fork; skipping to avoid exposing secrets.');
      core.setOutput('skip', 'true');
      return;
    }

    const prNumber = parsePrNumber(context);
    const diff = await collectPrDiff(github, context, prNumber);

    core.setOutput('pr_number', String(prNumber));
    core.setOutput('diff', diff);
    core.setOutput('skip', 'false');
  } catch (error) {
    core.setOutput('skip', 'true');
    core.setFailed(`Failed to resolve PR context: ${sanitizeError(error)}`);
  }
}

/**
 * Parse the response body only when it is JSON; otherwise return a safe string.
 * @param {Response} response
 * @returns {Promise<object | string | undefined>}
 */
async function parseResponseBody(response) {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try {
      return await response.json();
    } catch (error) {
      return { message: `Failed to parse JSON response: ${sanitizeError(error)}` };
    }
  }

  try {
    const text = await response.text();
    return text.length > 4000 ? `${text.slice(0, 4000)}...` : text;
  } catch (error) {
    return { message: `Unable to read response body: ${sanitizeError(error)}` };
  }
}

/**
 * Fetch with basic retry/backoff to reduce rate limit flakiness.
 * @param {string} url
 * @param {RequestInit} options
 * @param {{ attempts?: number, initialDelayMs?: number }} config
 * @returns {Promise<Response>}
 */
async function fetchWithRetry(url, options, config = {}) {
  const attempts = config.attempts ?? 3;
  const initialDelayMs = config.initialDelayMs ?? 1000;
  let lastError;

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(url, options);
      if (response.status === 429 || response.status >= 500) {
        lastError = new Error(`Received retryable status ${response.status}`);
      } else {
        return response;
      }
    } catch (error) {
      lastError = error;
    }

    if (attempt < attempts) {
      const delay = initialDelayMs * attempt;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

module.exports = {
  collectPrDiff,
  fetchWithRetry,
  parsePrNumber,
  parseResponseBody,
  resolvePrContext,
  sanitizeError,
};

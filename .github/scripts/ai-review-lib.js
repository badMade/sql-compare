'use strict';

/**
 * Extracts the PR number from the GitHub context.
 */
function getPrNumber(context) {
  const prNumber = context.payload.pull_request?.number || context.payload.issue?.number;
  if (!prNumber) {
    return null;
  }
  return prNumber;
}

/**
 * Fetches the diff for a pull request with pagination.
 */
async function getPrDiff(github, context, prNumber) {
  let files = [];
  let page = 1;
  while (true) {
    const { data: pageFiles } = await github.rest.pulls.listFiles({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber,
      per_page: 100,
      page: page,
    });
    files = files.concat(pageFiles);
    if (pageFiles.length < 100) break;
    page++;
    if (page > 10) break; // Safety limit: max 1000 files
  }

  return files.map(f =>
    `--- ${f.filename}\n+++ ${f.filename}\n${f.patch || '(binary)'}`
  ).join('\n\n');
}

/**
 * Standardized error handler that logs safely and fails the action.
 */
function fail(core, message, error) {
  let fullMessage = message;
  if (error) {
    const errorString = error.message || String(error);
    const truncatedError = errorString.length > 500 ? errorString.substring(0, 500) + '...' : errorString;
    fullMessage += `: ${truncatedError}`;
  }
  console.error(fullMessage);
  core.setFailed(message);
}

/**
 * A wrapper around fetch with retry logic and error sanitization.
 */
async function safeFetch(url, options, logger = console) {
  let lastError;
  const maxRetries = 3;
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        const contentType = response.headers.get('content-type');
        let errorBody = '';
        try {
          if (contentType && contentType.includes('application/json')) {
            const json = await response.json();
            errorBody = JSON.stringify(json);
          } else {
            errorBody = await response.text();
          }
        } catch (e) {
          errorBody = '(could not parse error body)';
        }

        // Sanitize error body to avoid secret exposure
        const sanitizedError = errorBody
          .replace(/key=[^&\s]+/g, 'key=[REDACTED]')
          .replace(/Authorization: Bearer [^\s&]+/gi, 'Authorization: Bearer [REDACTED]')
          .replace(/x-goog-api-key: [^\s&]+/gi, 'x-goog-api-key: [REDACTED]')
          .substring(0, 500);

        throw new Error(`HTTP ${response.status}: ${sanitizedError}`);
      }
      return response;
    } catch (error) {
      lastError = error;
      logger.info(`Fetch attempt ${i + 1} failed: ${error.message}`);
      if (i < maxRetries - 1) {
        const delay = Math.pow(2, i) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  throw lastError;
}

module.exports = {
  getPrNumber,
  getPrDiff,
  fail,
  safeFetch,
};

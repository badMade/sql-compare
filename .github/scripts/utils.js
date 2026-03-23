/**
 * Shared utilities for GitHub Actions workflows.
 */

/**
 * Extracts PR number and diff from the GitHub context.
 * @param {object} github - The GitHub object from actions/github-script.
 * @param {object} context - The context object from actions/github-script.
 * @param {object} core - The core object from actions/github-script.
 * @returns {Promise<{prNumber: number, diff: string}>}
 */
async function getPrInfo(github, context) {
  const prNumber = context.payload.pull_request?.number || context.payload.issue?.number;
  if (!prNumber || !Number.isInteger(Number(prNumber))) {
    throw new Error('Could not determine a valid PR number');
  }

  if (context.eventName === 'issue_comment' && !context.payload.issue.pull_request) {
    console.log('Comment on a regular issue, skipping.');
    return { prNumber: null, diff: '' };
  }

  const files = await github.paginate(github.rest.pulls.listFiles, {
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: prNumber,
    per_page: 100,
  });

  const diff = files.map(f =>
    `--- ${f.filename}\n+++ ${f.filename}\n${f.patch || '(binary)'}`
  ).join('\n\n');

  return { prNumber: Number(prNumber), diff };
}

/**
 * Safely extracts and truncates an error message.
 * @param {any} error - The error object or message.
 * @param {number} maxLength - Maximum length of the message (default 200).
 * @returns {string}
 */
function formatError(error, maxLength = 200) {
  let message = '';
  if (error instanceof Error) {
    message = error.message;
  } else if (typeof error === 'object' && error !== null) {
    try {
      message = error.message || JSON.stringify(error);
    } catch {
      message = String(error);
    }
  } else {
    message = String(error);
  }

  if (message.length > maxLength) {
    return message.substring(0, maxLength) + '... (truncated)';
  }
  return message;
}

/**
 * Performs an AI API call with safety checks.
 * @param {string} url - The API endpoint URL.
 * @param {object} options - Fetch options (method, headers, body).
 * @param {object} core - The core object from actions/github-script.
 * @returns {Promise<object>}
 */
async function callAiApi(url, options) {
  const response = await fetch(url, options);

  if (!response.ok) {
    let errorDetail = '';
    try {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const errorJson = await response.json();
        errorDetail = JSON.stringify(errorJson);
      } else {
        errorDetail = await response.text();
      }
    } catch (e) {
      errorDetail = 'Failed to parse error response';
    }
    throw new Error(`API request failed with status ${response.status}: ${formatError(errorDetail)}`);
  }

  const contentType = response.headers.get('content-type');
  if (!contentType || !contentType.includes('application/json')) {
    throw new Error(`API response was not JSON. Content-Type: ${contentType}`);
  }

  try {
    return await response.json();
  } catch (e) {
    throw new Error(`Failed to parse API response as JSON: ${formatError(e)}`);
  }
}

module.exports = {
  getPrInfo,
  formatError,
  callAiApi
};

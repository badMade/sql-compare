const MAX_ERROR_CHARS = 500;
const DEFAULT_PER_PAGE = 100;
const DEFAULT_MAX_PAGES = 10;
const DEFAULT_MAX_RETRIES = 2;

function safeErrorMessage(error, maxLength = MAX_ERROR_CHARS) {
  const message =
    (error && error.message) ||
    (typeof error === 'string' ? error : '') ||
    String(error || 'Unknown error');
  return message.length > maxLength ? `${message.slice(0, maxLength)}...` : message;
}

function truncateMessage(message, maxLength = MAX_ERROR_CHARS) {
  const normalized = typeof message === 'string' ? message : message ? String(message) : '';
  return normalized.length > maxLength ? `${normalized.substring(0, maxLength)}...` : normalized;
}

function formatError(error, maxLength = MAX_ERROR_CHARS) {
  return truncateMessage(safeErrorMessage(error, maxLength * 2), maxLength);
}

function validatePrNumber(rawNumber) {
  const parsed = parseInt(rawNumber, 10);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new Error('Invalid pull request number.');
  }
  return parsed;
}

function normalizePrNumber(rawNumber) {
  const prNumber = Number.parseInt(rawNumber, 10);
  if (!Number.isInteger(prNumber) || prNumber <= 0) {
    throw new Error('Invalid pull request number.');
  }
  return prNumber;
}

function parsePrNumber(payload) {
  const raw = payload?.pull_request?.number ?? payload?.issue?.number;
  if (raw === undefined || raw === null) {
    throw new Error('Could not determine pull request number from event payload.');
  }
  return validatePrNumber(raw);
}

async function fetchPrFilesWithPagination(
  github,
  context,
  prNumber,
  core,
  perPage = DEFAULT_PER_PAGE,
  maxPages = DEFAULT_MAX_PAGES
) {
  const files = [];
  for (let page = 1; page <= maxPages; page += 1) {
    const { data: pageFiles } = await github.rest.pulls.listFiles({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber,
      per_page: perPage,
      page,
    });
    files.push(...pageFiles);
    if (pageFiles.length < perPage) {
      break;
    }
    if (page === maxPages) {
      const errorMsg = `Reached pagination cap (${maxPages} pages) while fetching PR files.`;
      if (core) {
        core.warning(errorMsg);
      }
      throw new Error(errorMsg);
    }
  }
  return files;
}

function buildDiffString(files) {
  return files
    .map((file) => `--- ${file.filename}\n+++ ${file.filename}\n${file.patch || '(binary)'}`)
    .join('\n\n');
}

function isJsonResponse(response) {
  const contentType = response?.headers?.get?.('content-type');
  return typeof contentType === 'string' && contentType.toLowerCase().includes('application/json');
}

async function safeReadBody(response, maxLength = MAX_ERROR_CHARS) {
  if (!response) {
    return 'No response received.';
  }
  try {
    if (isJsonResponse(response)) {
      const json = await response.json();
      const jsonText = JSON.stringify(json);
      return jsonText.length > maxLength ? `${jsonText.slice(0, maxLength)}...` : jsonText;
    }
    const text = await response.text();
    if (!text) {
      return 'Empty response body.';
    }
    return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
  } catch (error) {
    return `Failed to read response body: ${safeErrorMessage(error, maxLength)}`;
  }
}

async function parseJsonResponse(response, maxLength = MAX_ERROR_CHARS) {
  const contentType = response?.headers?.get?.('content-type') || '';
  if (!contentType.toLowerCase().includes('application/json')) {
    const bodyText = await safeReadBody(response, maxLength);
    throw new Error(
      `Unexpected content-type: ${contentType || 'missing'}; truncated body: ${truncateMessage(
        bodyText,
        maxLength
      )}`
    );
  }
  return response.json();
}

async function fetchWithRetry(requestFn, options = {}) {
  const {
    retries,
    maxRetries = retries ?? DEFAULT_MAX_RETRIES,
    delayMs = 2000,
    shouldRetry = (response) => response && (response.status === 429 || response.status >= 500),
  } = options;

  let attempt = 0;
  while (true) {
    attempt += 1;
    try {
      const response = await requestFn();
      if (shouldRetry(response) && attempt <= maxRetries) {
        if (delayMs) {
          await new Promise((resolve) => setTimeout(resolve, delayMs));
        }
        continue;
      }
      return response;
    } catch (error) {
      if (attempt > maxRetries) {
        throw error;
      }
      if (delayMs) {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }
  }
}

module.exports = {
  buildDiffString,
  fetchPrFilesWithPagination,
  fetchWithRetry,
  formatError,
  isJsonResponse,
  normalizePrNumber,
  parseJsonResponse,
  parsePrNumber,
  safeErrorMessage,
  safeReadBody,
  truncateMessage,
  validatePrNumber,
};

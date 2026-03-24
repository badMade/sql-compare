'use strict';

const {
  buildDiffString,
  fetchPrFilesWithPagination,
  fetchWithRetry,
  isJsonResponse,
  normalizePrNumber,
  parsePrNumber,
  safeErrorMessage,
  safeReadBody,
} = require('./review-utils');

let passed = 0;
let failed = 0;

function assert(condition, label) {
  if (condition) {
    passed++;
  } else {
    failed++;
    console.error(`FAIL: ${label}`);
  }
}

function assertThrows(fn, label) {
  try {
    fn();
    failed++;
    console.error(`FAIL (no throw): ${label}`);
  } catch {
    passed++;
  }
}

// --- parsePrNumber ---
assert(parsePrNumber({ pull_request: { number: 42 } }) === 42, 'parsePrNumber from pull_request');
assert(parsePrNumber({ issue: { number: 7 } }) === 7, 'parsePrNumber from issue');
assert(parsePrNumber({ pull_request: { number: 1 }, issue: { number: 2 } }) === 1, 'parsePrNumber prefers pull_request');
assertThrows(() => parsePrNumber({}), 'parsePrNumber throws on empty payload');
assertThrows(() => parsePrNumber({ issue: {} }), 'parsePrNumber throws when no number');

// --- normalizePrNumber ---
assert(normalizePrNumber('42') === 42, 'normalizePrNumber string');
assert(normalizePrNumber(42) === 42, 'normalizePrNumber number');
assertThrows(() => normalizePrNumber(''), 'normalizePrNumber empty string');
assertThrows(() => normalizePrNumber(undefined), 'normalizePrNumber undefined');
assertThrows(() => normalizePrNumber('abc'), 'normalizePrNumber non-numeric');
assertThrows(() => normalizePrNumber(NaN), 'normalizePrNumber NaN');
assertThrows(() => normalizePrNumber(Infinity), 'normalizePrNumber Infinity');

// --- buildDiffString ---
assert(
  buildDiffString([
    { filename: 'a.js', patch: '@@ -1 +1 @@\n-old\n+new' },
    { filename: 'b.bin', patch: undefined },
  ]) === '--- a.js\n+++ a.js\n@@ -1 +1 @@\n-old\n+new\n\n--- b.bin\n+++ b.bin\n(binary)',
  'buildDiffString with patch and binary'
);
assert(buildDiffString([]) === '', 'buildDiffString empty');

// --- isJsonResponse ---
const makeResponse = (ct) => ({ headers: { get: () => ct } });
assert(isJsonResponse(makeResponse('application/json')) === true, 'isJsonResponse true');
assert(isJsonResponse(makeResponse('application/json; charset=utf-8')) === true, 'isJsonResponse with charset');
assert(isJsonResponse(makeResponse('text/html')) === false, 'isJsonResponse false');
assert(isJsonResponse(null) === false, 'isJsonResponse null');
assert(isJsonResponse({}) === false, 'isJsonResponse no headers');

// --- safeErrorMessage ---
assert(safeErrorMessage(new Error('boom')) === 'boom', 'safeErrorMessage Error');
assert(safeErrorMessage({ message: 'oops' }) === 'oops', 'safeErrorMessage object');
assert(safeErrorMessage('raw string') === 'raw string', 'safeErrorMessage string');
assert(safeErrorMessage(null) === 'null', 'safeErrorMessage null');
assert(safeErrorMessage(undefined) === 'undefined', 'safeErrorMessage undefined');

// --- safeReadBody ---
(async () => {
  const okResp = { text: async () => 'body text' };
  assert(await safeReadBody(okResp) === 'body text', 'safeReadBody success');
  const badResp = { text: async () => { throw new Error('fail'); } };
  assert(await safeReadBody(badResp) === '(unable to read response body)', 'safeReadBody failure');

  // --- fetchWithRetry ---
  let attempts = 0;
  const result = await fetchWithRetry(
    () => {
      attempts++;
      if (attempts < 3) throw new Error('transient');
      return Promise.resolve('ok');
    },
    { retries: 2, delayMs: 10 }
  );
  assert(result === 'ok', 'fetchWithRetry succeeds after retries');
  assert(attempts === 3, 'fetchWithRetry retried correct number of times');

  let failAttempts = 0;
  try {
    await fetchWithRetry(
      () => { failAttempts++; throw new Error('permanent'); },
      { retries: 1, delayMs: 10 }
    );
    assert(false, 'fetchWithRetry should throw after exhausting retries');
  } catch (e) {
    assert(e.message === 'permanent', 'fetchWithRetry throws last error');
    assert(failAttempts === 2, 'fetchWithRetry attempted correct times before failing');
  }

  // --- fetchPrFilesWithPagination fork check ---
  const mockCore = { info: () => {} };
  const mockGithub = {
    rest: {
      pulls: {
        get: async () => ({ data: { head: { repo: { full_name: 'fork/repo' } } } }),
        listFiles: async () => ({ data: [] }),
      },
    },
  };
  const mockContext = {
    eventName: 'issue_comment',
    repo: { owner: 'owner', repo: 'repo' },
  };
  const forkFiles = await fetchPrFilesWithPagination(mockGithub, mockContext, 1, mockCore);
  assert(forkFiles.length === 0, 'fetchPrFilesWithPagination returns empty for fork PRs');

  // fetchPrFilesWithPagination normal case
  const mockGithub2 = {
    rest: {
      pulls: {
        get: async () => ({ data: { head: { repo: { full_name: 'owner/repo' } } } }),
        listFiles: async ({ page }) => {
          if (page === 1) return { data: [{ filename: 'a.js', patch: '+a' }] };
          return { data: [] };
        },
      },
    },
  };
  const normalFiles = await fetchPrFilesWithPagination(mockGithub2, mockContext, 1, mockCore);
  assert(normalFiles.length === 1, 'fetchPrFilesWithPagination fetches files for internal PR');

  // --- Summary ---
  console.log(`\nResults: ${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
})();

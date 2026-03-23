'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { requestTeamReviews } = require('./auto-assign-reviewers');

function createLogger() {
  const entries = [];
  return {
    entries,
    info(message) {
      entries.push({ level: 'info', message });
    },
    error(message) {
      entries.push({ level: 'error', message });
    },
  };
}

function createContext(prNumber) {
  return {
    payload: {
      pull_request: prNumber === undefined ? undefined : { number: prNumber },
    },
    repo: {
      owner: 'badMade',
      repo: 'sql-compare',
    },
  };
}

test('fails fast when the pull request payload is missing', async () => {
  const logger = createLogger();
  const failures = [];
  const result = await requestTeamReviews({
    github: { rest: { pulls: { requestReviewers: async () => assert.fail('should not be called') } } },
    context: createContext(undefined),
    core: { setFailed: (message) => failures.push(message) },
    teamReviewers: ['team-a'],
    logger,
  });

  assert.equal(result.status, 'failed');
  assert.deepEqual(failures, ['Pull request number not found in the workflow payload.']);
  assert.match(logger.entries[0].message, /Pull request number not found/);
});

test('requests all configured teams when the initial call succeeds', async () => {
  const logger = createLogger();
  const calls = [];
  const github = {
    rest: {
      pulls: {
        requestReviewers: async (params) => {
          calls.push(params);
        },
      },
    },
  };

  const result = await requestTeamReviews({
    github,
    context: createContext(12),
    core: { setFailed: () => assert.fail('setFailed should not be called') },
    teamReviewers: ['team-a', 'team-b'],
    logger,
  });

  assert.equal(result.status, 'requested');
  assert.deepEqual(result.requestedTeams, ['team-a', 'team-b']);
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0].team_reviewers, ['team-a', 'team-b']);
});

test('filters invalid teams after a 422 and retries with valid teams only', async () => {
  const logger = createLogger();
  const calls = [];
  const github = {
    rest: {
      pulls: {
        requestReviewers: async (params) => {
          calls.push(params.team_reviewers);
          if (params.team_reviewers.length > 1) {
            const error = new Error('Reviews may only be requested from collaborators.');
            error.status = 422;
            throw error;
          }

          if (params.team_reviewers[0] === 'team-b') {
            const error = new Error('team-b is not a collaborator');
            error.status = 422;
            throw error;
          }
        },
      },
    },
  };

  const result = await requestTeamReviews({
    github,
    context: createContext(34),
    core: { setFailed: () => assert.fail('setFailed should not be called') },
    teamReviewers: ['team-a', 'team-b', 'team-c'],
    logger,
  });

  assert.equal(result.status, 'requested');
  assert.deepEqual(result.requestedTeams, ['team-a', 'team-c']);
  assert.deepEqual(result.skippedTeams, ['team-b']);
  assert.deepEqual(calls, [
    ['team-a', 'team-b', 'team-c'],
    ['team-a'],
    ['team-b'],
    ['team-c'],
  ]);
  assert.match(
    logger.entries.map((entry) => entry.message).join('\n'),
    /Skipped invalid team reviewers: team-b/
  );
});

test('fails the workflow on unexpected API errors', async () => {
  const logger = createLogger();
  const failures = [];
  const github = {
    rest: {
      pulls: {
        requestReviewers: async () => {
          const error = new Error('GitHub API unavailable');
          error.status = 503;
          throw error;
        },
      },
    },
  };

  const result = await requestTeamReviews({
    github,
    context: createContext(55),
    core: { setFailed: (message) => failures.push(message) },
    teamReviewers: ['team-a'],
    logger,
  });

  assert.equal(result.status, 'failed');
  assert.deepEqual(failures, ['Failed to assign reviewers: GitHub API unavailable']);
});

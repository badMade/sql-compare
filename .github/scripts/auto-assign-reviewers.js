'use strict';

async function requestReviewersForTeams(github, context, prNumber, teamSlugs) {
  return github.rest.pulls.requestReviewers({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: prNumber,
    team_reviewers: teamSlugs,
  });
}

function normalizeErrorMessage(error) {
  if (!error) {
    return 'Unknown error';
  }

  if (typeof error.message === 'string' && error.message.trim()) {
    return error.message;
  }

  return String(error);
}

function isExpectedInvalidReviewerError(error) {
  return error && error.status === 422;
}

async function findRequestableTeams(github, context, prNumber, configuredTeamReviewers, logger) {
29:  const promises = configuredTeamReviewers.map(teamSlug =>
30:    requestReviewersForTeams(github, context, prNumber, [teamSlug])
31:  );
32:
33:  const results = await Promise.allSettled(promises);
34:
35:  const requestableTeams = [];
36:  const skippedTeams = [];
37:
38:  results.forEach((result, index) => {
39:    const teamSlug = configuredTeamReviewers[index];
40:    if (result.status === 'fulfilled') {
41:      requestableTeams.push(teamSlug);
42:    } else { // 'rejected'
43:      const error = result.reason;
44:      if (isExpectedInvalidReviewerError(error)) {
45:        skippedTeams.push(teamSlug);
46:        logger.info(`Skipping team reviewer '${teamSlug}' because GitHub rejected the review request.`);
47:      } else {
48:        logger.error(
49:          `Unexpected error while validating team reviewer '${teamSlug}': ${normalizeErrorMessage(error)}`
50:        );
51:        throw error;
52:      }
53:    }
54:  });
55:
56:  return { requestableTeams, skippedTeams };
}

async function requestTeamReviews({ github, context, core, teamReviewers, logger = console }) {
  const pullRequest = context && context.payload ? context.payload.pull_request : undefined;
  const prNumber = pullRequest ? pullRequest.number : undefined;

  if (!pullRequest || typeof prNumber !== 'number') {
    const message = 'Pull request number not found in the workflow payload.';
    logger.error(message);
    core.setFailed(message);
    return { status: 'failed', message };
  }

  if (!Array.isArray(teamReviewers) || teamReviewers.length === 0) {
    const message = 'No team reviewers are configured for this workflow run.';
    logger.info(message);
    return { status: 'skipped', message, requestedTeams: [], skippedTeams: [] };
  }

  try {
    await requestReviewersForTeams(github, context, prNumber, teamReviewers);
    logger.info(`Requested reviews from teams: ${teamReviewers.join(', ')}`);
    return { status: 'requested', requestedTeams: teamReviewers, skippedTeams: [] };
  } catch (error) {
    if (!isExpectedInvalidReviewerError(error)) {
      const message = `Failed to assign reviewers: ${normalizeErrorMessage(error)}`;
      logger.error(message);
      core.setFailed(message);
      return { status: 'failed', message, requestedTeams: [], skippedTeams: [] };
    }
  }

  try {
    const { requestableTeams, skippedTeams } = await findRequestableTeams(
      github,
      context,
      prNumber,
      teamReviewers,
      logger
    );

    if (requestableTeams.length === 0) {
      const skippedSummary = skippedTeams.length > 0 ? ` Skipped teams: ${skippedTeams.join(', ')}.` : '';
      const message = `No valid team reviewers remain after filtering invalid teams.${skippedSummary}`;
      logger.info(message);
      return { status: 'skipped', message, requestedTeams: [], skippedTeams };
    }

    logger.info(`Requested reviews from teams: ${requestableTeams.join(', ')}`);
    if (skippedTeams.length > 0) {
      logger.info(`Skipped invalid team reviewers: ${skippedTeams.join(', ')}`);
    }

    return { status: 'requested', requestedTeams: requestableTeams, skippedTeams };
  } catch (error) {
    const message = `Failed to assign reviewers: ${normalizeErrorMessage(error)}`;
    logger.error(message);
    core.setFailed(message);
    return { status: 'failed', message, requestedTeams: [], skippedTeams: [] };
  }
}

module.exports = {
  findRequestableTeams,
  isExpectedInvalidReviewerError,
  normalizeErrorMessage,
  requestReviewersForTeams,
  requestTeamReviews,
};

const DEFAULT_PER_PAGE = 100;
const DEFAULT_MAX_PAGES = 10;

function getPullRequestNumber(context) {
  const prNumber = context.payload.pull_request?.number || context.payload.issue?.number;
  if (!prNumber) {
    throw new Error('Could not determine PR number');
  }
  if (context.eventName === 'issue_comment' && !context.payload.issue?.pull_request) {
    throw new Error('Comment is not on a pull request');
  }
  return prNumber;
}

async function listPullRequestFiles({ github, context, core, perPage = DEFAULT_PER_PAGE, maxPages = DEFAULT_MAX_PAGES }) {
  const files = [];
  for (let page = 1; page <= maxPages; page += 1) {
    const { data } = await github.rest.pulls.listFiles({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: context.pullRequestNumber,
      per_page: perPage,
      page,
    });

    if (!Array.isArray(data) || data.length === 0) {
      break;
    }

    files.push(...data);
    core.debug(`Fetched ${data.length} files from page ${page}`);

    if (data.length < perPage) {
      break;
    }
  }

  if (files.length === perPage * maxPages) {
    core.info('Reached pull request file pagination limit; diff may be truncated.');
  }

  return files;
}

function buildDiff(files, core) {
  if (!files.length) {
    return '';
  }

  const diffParts = [];

  for (const file of files) {
    const header = `--- ${file.filename}\n+++ ${file.filename}\n`;
    if (typeof file.patch === 'string' && file.patch.length > 0) {
      diffParts.push(header + file.patch);
    } else {
      diffParts.push(header + '(binary file)');
    }
  }

  const diff = diffParts.join('\n\n');
  core.debug(`Constructed diff with ${diffParts.length} entries`);
  return diff;
}

async function fetchPullRequestDiff({ github, context, core, perPage = DEFAULT_PER_PAGE, maxPages = DEFAULT_MAX_PAGES }) {
  const prNumber = getPullRequestNumber(context);
  context.pullRequestNumber = prNumber;

  const files = await listPullRequestFiles({ github, context, core, perPage, maxPages });
  const diff = buildDiff(files, core);

  return { prNumber, diff, files };
}

module.exports = {
  fetchPullRequestDiff,
};

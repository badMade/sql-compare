'use strict';

const fs = require('fs');
const { fail, safeFetch } = require('./ai-review-lib.js');

module.exports = async ({ github, context, core }) => {
  const prNumber = Number(process.env.PR_NUMBER);
  const apiKey = process.env.OPENAI_API_KEY;

  if (!prNumber || prNumber < 1) {
    return fail(core, 'Invalid PR number provided.');
  }
  if (!apiKey) {
    return fail(core, 'OPENAI_API_KEY is not set.');
  }

  try {
    const diff = fs.readFileSync('pr_diff.txt', 'utf8');
    if (!diff) {
      console.log('Diff is empty, skipping review.');
      return;
    }

    console.log(`Sending PR #${prNumber} diff to OpenAI for review...`);

    const response = await safeFetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4o',
        messages: [
          {
            role: 'system',
            content: 'You are a code reviewer. Review the following PR diff. ' +
                     'Identify bugs, security issues, style problems, and suggest improvements. ' +
                     'Be concise and actionable.'
          },
          {
            role: 'user',
            content: `Please review this pull request diff:\n\n${diff}`
          }
        ],
        max_tokens: 4096,
      }),
    });

    const result = await response.json();
    const review = result.choices?.[0]?.message?.content || 'Unable to generate review.';

    await github.rest.pulls.createReview({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber,
      event: 'COMMENT',
      body: `## Codex Review\n\n${review}`,
    });

    console.log(`Successfully posted Codex review for PR #${prNumber}.`);
  } catch (error) {
    fail(core, 'Review process with Codex failed', error);
  }
};

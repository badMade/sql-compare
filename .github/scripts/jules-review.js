'use strict';

const fs = require('fs');
const { fail, safeFetch } = require('./ai-review-lib.js');

module.exports = async ({ github, context, core }) => {
  const prNumber = Number(process.env.PR_NUMBER);
  const apiKey = process.env.GOOGLE_API_KEY;

  if (!prNumber || prNumber < 1) {
    return fail(core, 'Invalid PR number provided.');
  }
  if (!apiKey) {
    return fail(core, 'GOOGLE_API_KEY is not set.');
  }

  try {
    const diff = fs.readFileSync('pr_diff.txt', 'utf8');
    if (!diff) {
      console.log('Diff is empty, skipping review.');
      return;
    }

    console.log(`Sending PR #${prNumber} diff to Gemini for review...`);

    const response = await safeFetch(
      'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-goog-api-key': apiKey,
        },
        body: JSON.stringify({
          contents: [{
            parts: [{
              text: `You are a code reviewer. Review the following PR diff. ` +
                    `Identify bugs, security issues, style problems, and suggest improvements. ` +
                    `Be concise and actionable.\n\nPR Diff:\n${diff}`
            }]
          }],
          generationConfig: { maxOutputTokens: 4096 },
        }),
      }
    );

    const result = await response.json();
    const review = result.candidates?.[0]?.content?.parts?.[0]?.text || 'Unable to generate review.';

    await github.rest.pulls.createReview({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber,
      event: 'COMMENT',
      body: `## Jules Review\n\n${review}`,
    });

    console.log(`Successfully posted Jules review for PR #${prNumber}.`);
  } catch (error) {
    fail(core, 'Review process with Gemini failed', error);
  }
};

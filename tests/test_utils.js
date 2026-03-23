const assert = require('assert');
const utils = require('../.github/scripts/utils.js');

/**
 * Mock global fetch.
 */
global.fetch = async (url, options) => {
  if (url === 'https://api.openai.com/v1/chat/completions') {
    return {
      ok: true,
      headers: new Map([['content-type', 'application/json']]),
      json: async () => ({ choices: [{ message: { content: 'mocked review' } }] })
    };
  } else if (url === 'https://error.com') {
    return {
      ok: false,
      status: 400,
      headers: new Map([['content-type', 'application/json']]),
      json: async () => ({ error: 'bad request' })
    };
  } else if (url === 'https://text.com') {
    return {
      ok: false,
      status: 500,
      headers: new Map([['content-type', 'text/plain']]),
      text: async () => 'internal server error'
    };
  } else if (url === 'https://notjson.com') {
    return {
      ok: true,
      headers: new Map([['content-type', 'text/html']]),
      text: async () => '<html></html>'
    };
  }
};


async function testShouldTrigger() {
  console.log('Testing shouldTrigger...');
  assert.strictEqual(utils.shouldTrigger({ eventName: 'pull_request', payload: {} }, '@codex'), true);
  assert.strictEqual(
    utils.shouldTrigger(
      { eventName: 'issue_comment', payload: { comment: { body: 'Please review this @codex' } } },
      '@codex'
    ),
    true
  );
  assert.strictEqual(
    utils.shouldTrigger(
      { eventName: 'pull_request_review_comment', payload: { comment: { body: 'Hello @jules' } } },
      '@codex'
    ),
    false
  );
  assert.strictEqual(utils.shouldTrigger(null, '@codex'), false);
}

async function testFormatError() {
  console.log('Testing formatError...');
  assert.strictEqual(utils.formatError('small error'), 'small error');
  assert.strictEqual(utils.formatError(new Error('error instance')), 'error instance');
  const longError = 'a'.repeat(250);
  assert.strictEqual(utils.formatError(longError, 200), 'a'.repeat(200) + '... (truncated)');
  assert.strictEqual(utils.formatError({ message: 'obj error' }), 'obj error');
  assert.strictEqual(utils.formatError({ foo: 'bar' }), '{"foo":"bar"}');
  const circular = {};
  circular.ref = circular;
  assert.strictEqual(utils.formatError(circular), '[object Object]');
}

async function testGetPrInfo() {
  console.log('Testing getPrInfo...');
  const mockGithub = {
    paginate: async (_method, _options) => ([
      { filename: 'test.py', patch: '@@ -1,1 +1,1 @@\n-old\n+new' }
    ]),
    rest: {
      pulls: {
        listFiles: async () => ({
          data: [{ filename: 'test.py', patch: '@@ -1,1 +1,1 @@\n-old\n+new' }]
        })
      }
    }
  };

  const mockContext = {
    payload: { pull_request: { number: 123 } },
    repo: { owner: 'user', repo: 'repo' }
  };

  const info = await utils.getPrInfo(mockGithub, mockContext, {});
  assert.strictEqual(info.prNumber, 123);
  assert.ok(info.diff.includes('--- test.py'));
  assert.ok(info.diff.includes('+new'));
}

async function testCallAiApi() {
  console.log('Testing callAiApi...');

  // Success
  const result = await utils.callAiApi('https://api.openai.com/v1/chat/completions', {}, {});
  assert.strictEqual(result.choices[0].message.content, 'mocked review');

  // Error 400 JSON
  try {
    await utils.callAiApi('https://error.com', {}, {});
    assert.fail('Should have thrown an error');
  } catch (e) {
    assert.ok(e.message.includes('status 400'));
    assert.ok(e.message.includes('bad request'));
  }

  // Error 500 Text
  try {
    await utils.callAiApi('https://text.com', {}, {});
    assert.fail('Should have thrown an error');
  } catch (e) {
    assert.ok(e.message.includes('status 500'));
    assert.ok(e.message.includes('internal server error'));
  }

  // Not JSON
  try {
    await utils.callAiApi('https://notjson.com', {}, {});
    assert.fail('Should have thrown an error');
  } catch (e) {
    assert.ok(e.message.includes('was not JSON'));
  }
}

async function runTests() {
  try {
    await testShouldTrigger();
    await testFormatError();
    await testGetPrInfo();
    await testCallAiApi();
    console.log('All utility tests passed!');
  } catch (e) {
    console.error('Test failed:', e);
    process.exit(1);
  }
}

runTests();

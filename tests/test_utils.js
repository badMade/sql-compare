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

  // Mock that simulates single-page results via github.paginate
  const mockGithub = {
    paginate: async (fn, params) => {
      const result = await fn(params);
      return result.data;
    },
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

  const info = await utils.getPrInfo(mockGithub, mockContext);
  assert.strictEqual(info.prNumber, 123);
  assert.ok(info.diff.includes('--- test.py'));
  assert.ok(info.diff.includes('+new'));
}

async function testGetPrInfoPagination() {
  console.log('Testing getPrInfo pagination (multiple pages)...');

  // Simulate a PR with files across two pages
  const page1Files = Array.from({ length: 100 }, (_, i) => ({
    filename: `file_page1_${i}.py`,
    patch: `@@ -1,1 +1,1 @@\n-old${i}\n+new${i}`
  }));
  const page2Files = [
    { filename: 'file_page2_0.py', patch: '@@ -1,1 +1,1 @@\n-oldX\n+newX' }
  ];
  const allFiles = [...page1Files, ...page2Files];

  let paginateCalled = false;
  // github.paginate returns a flat array of all items across all pages
  const mockGithub = {
    paginate: async (fn, params) => {
      paginateCalled = true;
      // Invoke fn to verify the correct function is passed
      assert.ok(typeof fn === 'function', 'paginate should receive a function');
      assert.strictEqual(params.pull_number, 456);
      return allFiles;
    },
    rest: {
      pulls: {
        // listFiles should not be called directly; throw if it is
        listFiles: async () => {
          throw new Error('listFiles called directly instead of via paginate');
        }
      }
    }
  };

  const mockContext = {
    payload: { pull_request: { number: 456 } },
    repo: { owner: 'user', repo: 'repo' }
  };

  const info = await utils.getPrInfo(mockGithub, mockContext);
  assert.ok(paginateCalled, 'github.paginate should have been called');
  assert.strictEqual(info.prNumber, 456);
  // All 101 files should be present in the diff
  assert.strictEqual((info.diff.match(/^--- /mg) || []).length, 101);
  assert.ok(info.diff.includes('--- file_page1_0.py'));
  assert.ok(info.diff.includes('--- file_page2_0.py'));
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
    await testFormatError();
    await testGetPrInfo();
    await testGetPrInfoPagination();
    await testCallAiApi();
    console.log('All utility tests passed!');
  } catch (e) {
    console.error('Test failed:', e);
    process.exit(1);
  }
}

runTests();

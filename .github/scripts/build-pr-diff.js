#!/usr/bin/env node

function buildDiff(files) {
  if (!Array.isArray(files)) {
    throw new Error('Invalid file list: expected an array');
  }

  return files
    .map((file) => {
      if (!file || typeof file.filename !== 'string') {
        throw new Error('Invalid file entry: missing filename');
      }

      const header = `--- ${file.filename}\n+++ ${file.filename}\n`;
      const patch =
        typeof file.patch === 'string' && file.patch.length > 0
          ? file.patch
          : '(binary)';

      return `${header}${patch}`;
    })
    .join('\n\n');
}

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf-8');
    process.stdin.on('data', (chunk) => {
      data += chunk;
    });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', reject);
  });
}

async function main() {
  try {
    const raw = await readStdin();
    const parsed = raw.trim() ? JSON.parse(raw) : [];
    const diff = buildDiff(parsed);
    if (diff) {
      process.stdout.write(diff);
    }
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
} else {
  module.exports = { buildDiff };
}

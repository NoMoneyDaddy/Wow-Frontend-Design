#!/usr/bin/env node
'use strict';

const path = require('node:path');
const { spawnSync } = require('node:child_process');

function fail(message) {
  console.error(`vnu preflight failed: ${message}`);
  process.exit(2);
}

const version = spawnSync('java', ['-version'], { encoding: 'utf8' });
if (version.error || version.status !== 0) {
  fail('Java 11 or newer must already be installed; no runtime will be downloaded automatically.');
}

const versionOutput = `${version.stdout || ''}\n${version.stderr || ''}`;
const match = versionOutput.match(/version "(?:1\.)?(\d+)/);
if (!match || Number(match[1]) < 11) {
  fail('Java 11 or newer is required.');
}

let vnuEntry;
try {
  vnuEntry = require.resolve('vnu-jar');
} catch {
  fail('vnu-jar is not installed; run npm ci --ignore-scripts.');
}

const jar = path.join(path.dirname(vnuEntry), 'build', 'dist', 'vnu.jar');
const result = spawnSync('java', ['-jar', jar, ...process.argv.slice(2)], {
  stdio: 'inherit',
});

if (result.error) {
  fail(result.error.message);
}
process.exit(result.status ?? 1);

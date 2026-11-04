// P6 security regression. Runs outside Vitest so compilation has a hard process
// deadline and cannot hang the test runner on vulnerable pattern amplification.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import process from 'node:process';
import console from 'node:console';
import { URL } from 'node:url';

const require = createRequire(import.meta.url);
const lock = JSON.parse(readFileSync(new URL('../package-lock.json', import.meta.url)));
const matchers = Object.entries(lock.packages).filter(([p]) => /node_modules\/minimatch$/.test(p));
assert.equal(matchers.length, 1);
assert.equal(matchers[0][1].version, '11.0.1');
assert.equal(matchers[0][1].dev, true);
for (const consumer of ['eslint', '@eslint/config-array', '@typescript-eslint/typescript-estree']) {
  const consumerRequire = createRequire(require.resolve(consumer));
  assert.equal(consumerRequire('minimatch/package.json').version, '11.0.1');
  const { minimatch } = consumerRequire('minimatch');
  assert(minimatch('src/file.ts', '**/*.ts', { dot: true }));
  assert(!minimatch('src/file.js', '**/*.ts'));
}
const result = spawnSync(process.execPath, ['--input-type=module', '-e', `
  import { Minimatch } from 'minimatch';
  const pattern = '**/../'.repeat(22) + '*.ts';
  for (const optimizationLevel of [0, 1, 2]) {
    const matcher = new Minimatch(pattern, { optimizationLevel });
    matcher.match('src/file.ts');
  }
`], { cwd: new URL('..', import.meta.url), timeout: 5000, encoding: 'utf8' });
assert.equal(result.error, undefined, 'adversarial compilation exceeded process budget');
assert.equal(result.status, 0, 'adversarial compilation failed');
console.log('PASS: fixed resolution for all three consumers; normal and adversarial glob compilation');

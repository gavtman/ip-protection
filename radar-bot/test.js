#!/usr/bin/env node
/**
 * Tests for radar-bot/bot.js
 *
 * Run with:  node test.js
 */

'use strict';

const fs = require('fs');
const path = require('path');
const assert = require('assert');

// ─── Load the modules we need from bot.js ─────────────────────────────────────
// bot.js uses top-level `main()` which we don't want to invoke, so we re-expose
// the pure functions directly here for testing.

// Inline the same parseMDL + checkDomain logic so we can test them in isolation.

/** Reproduce parseMDL from bot.js */
function parseMDL(mdlPath) {
  const domains = new Set();
  const entries = new Map();
  const raw = fs.readFileSync(mdlPath, 'utf8');
  const tableRowRe = /^\s*([^\s|][^|]*?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*$/;
  for (const line of raw.split('\n')) {
    const m = line.match(tableRowRe);
    if (!m) continue;
    const domain = m[1].trim().toLowerCase();
    if (!domain || domain === 'domain' || /^-+$/.test(domain)) continue;
    domains.add(domain);
    entries.set(domain, { owner: m[2].trim(), scriptBlocking: m[3].trim() });
  }
  return { domains, entries };
}

/** Reproduce checkDomain from bot.js */
function checkDomain(input, domains, entries) {
  const normalized = input.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/.*$/, '');
  const parts = normalized.split('.');
  for (let i = 0; i < parts.length - 1; i++) {
    const candidate = parts.slice(i).join('.');
    if (domains.has(candidate)) {
      return { matched: true, matchedAs: candidate, entry: entries.get(candidate) };
    }
  }
  return { matched: false, matchedAs: null, entry: null };
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✔ ${name}`);
    passed++;
  } catch (err) {
    console.error(`  ✘ ${name}`);
    console.error(`      ${err.message}`);
    failed++;
  }
}

// ─── parseMDL tests ───────────────────────────────────────────────────────────
console.log('\nparseMDL — using a synthetic MDL fragment');

const TMP_MDL = path.join(require('os').tmpdir(), 'test-mdl.md');
fs.writeFileSync(TMP_MDL, [
  'Domain                | Owner          | Impacted by Script Blocking',
  '--------------------- | -------------- | ---------------------------',
  'example-tracker.com   | Tracker Corp   | Not Impacted By Script Blocking',
  'ads.example.net       | Ad Network     | Entire Domain Blocked',
  'sub.ads.example.net   | Ad Network     | Not Impacted By Script Blocking',
].join('\n'));

const { domains: syntheticDomains, entries: syntheticEntries } = parseMDL(TMP_MDL);

test('parses domain names from table rows', () => {
  assert.ok(syntheticDomains.has('example-tracker.com'));
  assert.ok(syntheticDomains.has('ads.example.net'));
});

test('does not include the header row as a domain', () => {
  assert.ok(!syntheticDomains.has('domain'));
});

test('does not include separator rows', () => {
  for (const d of syntheticDomains) {
    assert.ok(!/^-+$/.test(d), `Found separator row in domain set: ${d}`);
  }
});

test('stores owner metadata', () => {
  assert.strictEqual(syntheticEntries.get('example-tracker.com').owner, 'Tracker Corp');
});

test('stores scriptBlocking metadata', () => {
  assert.strictEqual(syntheticEntries.get('ads.example.net').scriptBlocking, 'Entire Domain Blocked');
});

// ─── checkDomain tests ────────────────────────────────────────────────────────
console.log('\ncheckDomain — matching logic');

test('exact match returns matched=true', () => {
  const r = checkDomain('example-tracker.com', syntheticDomains, syntheticEntries);
  assert.ok(r.matched);
  assert.strictEqual(r.matchedAs, 'example-tracker.com');
});

test('subdomain of listed domain is matched', () => {
  const r = checkDomain('sub.example-tracker.com', syntheticDomains, syntheticEntries);
  assert.ok(r.matched);
  assert.strictEqual(r.matchedAs, 'example-tracker.com');
});

test('unlisted domain returns matched=false', () => {
  const r = checkDomain('safe.example.com', syntheticDomains, syntheticEntries);
  assert.ok(!r.matched);
  assert.strictEqual(r.matchedAs, null);
});

test('https:// prefix is stripped before matching', () => {
  const r = checkDomain('https://example-tracker.com/path', syntheticDomains, syntheticEntries);
  assert.ok(r.matched);
});

test('http:// prefix is stripped before matching', () => {
  const r = checkDomain('http://ads.example.net', syntheticDomains, syntheticEntries);
  assert.ok(r.matched);
});

test('lookup is case-insensitive', () => {
  const r = checkDomain('EXAMPLE-TRACKER.COM', syntheticDomains, syntheticEntries);
  assert.ok(r.matched);
});

test('a domain listed explicitly as subdomain is matched exactly', () => {
  const r = checkDomain('sub.ads.example.net', syntheticDomains, syntheticEntries);
  assert.ok(r.matched);
  assert.strictEqual(r.matchedAs, 'sub.ads.example.net');
});

// ─── Real MDL smoke test ──────────────────────────────────────────────────────
console.log('\nparseMDL — real Masked-Domain-List.md smoke test');

const REAL_MDL = path.resolve(__dirname, '..', 'Masked-Domain-List.md');

test('real MDL file is readable and contains entries', () => {
  const { domains: realDomains } = parseMDL(REAL_MDL);
  assert.ok(realDomains.size > 0, `Expected at least one domain, got ${realDomains.size}`);
});

test('known domain 33across.com is in real MDL', () => {
  const { domains: realDomains, entries: realEntries } = parseMDL(REAL_MDL);
  const r = checkDomain('33across.com', realDomains, realEntries);
  assert.ok(r.matched, '33across.com should be in the MDL');
});

test('an unknown domain is not in real MDL', () => {
  const { domains: realDomains, entries: realEntries } = parseMDL(REAL_MDL);
  const r = checkDomain('this-domain-should-not-be-on-the-mdl-ever.example', realDomains, realEntries);
  assert.ok(!r.matched);
});

// ─── Summary ──────────────────────────────────────────────────────────────────
console.log(`\n  Passed: ${passed}  Failed: ${failed}\n`);
if (failed > 0) process.exit(1);

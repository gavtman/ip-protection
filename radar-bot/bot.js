#!/usr/bin/env node
/**
 * Radar Bot — IP Protection Masked Domain List scanner
 *
 * Usage:
 *   node bot.js <domain> [domain ...]
 *   node bot.js --file domains.txt
 *   node bot.js --interactive
 *
 * Reads Masked-Domain-List.md from the parent directory (or the path set by
 * the MDL_PATH environment variable) and reports whether each supplied domain
 * is on the list.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// ─── ANSI colours ────────────────────────────────────────────────────────────
const GREEN  = '\x1b[32m';
const RED    = '\x1b[31m';
const YELLOW = '\x1b[33m';
const CYAN   = '\x1b[36m';
const BOLD   = '\x1b[1m';
const DIM    = '\x1b[2m';
const RESET  = '\x1b[0m';

// ─── ASCII radar frame ────────────────────────────────────────────────────────
const RADAR_FRAME = `
${CYAN}${BOLD}        ___________
       /           \\
      /   .  .  .   \\
     |  .   [ ]   .  |
      \\   .  .  .   /
       \\___________/
      I P  P R O T E C T${RESET}
`;

// ─── Parse the Masked Domain List markdown table ──────────────────────────────
/**
 * @param {string} mdlPath  Absolute path to Masked-Domain-List.md
 * @returns {{ domains: Set<string>, entries: Map<string,{owner:string,scriptBlocking:string}> }}
 */
function parseMDL(mdlPath) {
  const domains = new Set();
  const entries = new Map();

  let raw;
  try {
    raw = fs.readFileSync(mdlPath, 'utf8');
  } catch (err) {
    throw new Error(`Cannot read MDL file at "${mdlPath}": ${err.message}`);
  }

  // The table rows look like:
  //   domain.com  | Owner Name  | Not Impacted By Script Blocking
  // Skip the header row (contains "Domain") and the separator row (contains dashes).
  const tableRowRe = /^\s*([^\s|][^|]*?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*$/;

  for (const line of raw.split('\n')) {
    const m = line.match(tableRowRe);
    if (!m) continue;
    const domain = m[1].trim().toLowerCase();
    if (!domain || domain === 'domain' || /^-+$/.test(domain)) continue;
    domains.add(domain);
    entries.set(domain, {
      owner: m[2].trim(),
      scriptBlocking: m[3].trim(),
    });
  }

  return { domains, entries };
}

// ─── Domain look-up ───────────────────────────────────────────────────────────
/**
 * Check a domain and all its parent domains against the MDL.
 * e.g. "sub.example.com" is checked as both "sub.example.com" and "example.com".
 *
 * @returns {{ matched: boolean, matchedAs: string|null, entry: object|null }}
 */
function checkDomain(input, domains, entries) {
  const normalized = input.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/.*$/, '');

  // Walk up the dot-hierarchy
  const parts = normalized.split('.');
  for (let i = 0; i < parts.length - 1; i++) {
    const candidate = parts.slice(i).join('.');
    if (domains.has(candidate)) {
      return { matched: true, matchedAs: candidate, entry: entries.get(candidate) };
    }
  }
  return { matched: false, matchedAs: null, entry: null };
}

// ─── Pretty output helpers ────────────────────────────────────────────────────
function printHeader() {
  console.log(RADAR_FRAME);
  console.log(`${BOLD}${CYAN}  📡 Radar Bot — IP Protection MDL Scanner${RESET}`);
  console.log(`${DIM}  Scanning domains against Chrome's Masked Domain List…${RESET}\n`);
}

function printResult(domain, result) {
  const { matched, matchedAs, entry } = result;
  const icon   = matched ? `${GREEN}✔` : `${RED}✘`;
  const status = matched ? `${GREEN}PROTECTED${RESET}` : `${RED}NOT PROTECTED${RESET}`;
  const label  = domain !== matchedAs && matchedAs ? ` ${DIM}(matched as ${matchedAs})${RESET}` : '';

  console.log(`  ${icon} ${BOLD}${domain}${RESET} — ${status}${label}`);
  if (matched && entry) {
    console.log(`      ${DIM}Owner: ${entry.owner}${RESET}`);
    console.log(`      ${DIM}Script blocking: ${entry.scriptBlocking}${RESET}`);
  }
}

function printSummary(total, protected_) {
  const unprotected = total - protected_;
  console.log(`\n${BOLD}─────────────────────────────────────────${RESET}`);
  console.log(`  Scanned : ${BOLD}${total}${RESET} domain${total !== 1 ? 's' : ''}`);
  console.log(`  ${GREEN}Protected   : ${BOLD}${protected_}${RESET}`);
  console.log(`  ${RED}Unprotected : ${BOLD}${unprotected}${RESET}`);
  console.log(`${BOLD}─────────────────────────────────────────${RESET}\n`);
}

// ─── Scan a list of domains and print results ──────────────────────────────────
function scanDomains(domainList, domains, entries) {
  let protectedCount = 0;
  for (const domain of domainList) {
    if (!domain.trim()) continue;
    const result = checkDomain(domain, domains, entries);
    printResult(domain, result);
    if (result.matched) protectedCount++;
  }
  return protectedCount;
}



// ─── Interactive REPL mode ────────────────────────────────────────────────────
async function interactiveMode(domains, entries) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: `${CYAN}radar>${RESET} `,
  });

  console.log(`${YELLOW}Interactive mode. Type a domain to scan, or "exit" to quit.${RESET}\n`);
  rl.prompt();

  rl.on('line', (line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      rl.prompt();
      return;
    }
    if (trimmed === 'exit' || trimmed === 'quit') {
      console.log(`${DIM}Goodbye.${RESET}`);
      rl.close();
      return;
    }
    const result = checkDomain(trimmed, domains, entries);
    printResult(trimmed, result);
    console.log();
    rl.prompt();
  });

  await new Promise((resolve) => rl.on('close', resolve));
}

// ─── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  const args = process.argv.slice(2);

  const mdlPath = process.env.MDL_PATH ||
    path.resolve(__dirname, '..', 'Masked-Domain-List.md');

  // Parse the MDL
  let mdl;
  try {
    mdl = parseMDL(mdlPath);
  } catch (err) {
    console.error(`${RED}Error: ${err.message}${RESET}`);
    process.exit(1);
  }

  const { domains, entries } = mdl;

  printHeader();
  console.log(`  ${DIM}MDL loaded: ${domains.size.toLocaleString()} domains from ${mdlPath}${RESET}\n`);

  // --interactive flag
  if (args.includes('--interactive') || args.includes('-i')) {
    await interactiveMode(domains, entries);
    return;
  }

  // --file <path> flag
  const fileIdx = args.findIndex((a) => a === '--file' || a === '-f');
  if (fileIdx !== -1) {
    const filePath = args[fileIdx + 1];
    if (!filePath) {
      console.error(`${RED}Error: --file requires a path argument${RESET}`);
      process.exit(1);
    }
    let fileContent;
    try {
      fileContent = fs.readFileSync(filePath, 'utf8');
    } catch (err) {
      console.error(`${RED}Error reading file "${filePath}": ${err.message}${RESET}`);
      process.exit(1);
    }
    const list = fileContent.split(/\r?\n/).filter(Boolean);
    const protectedCount = scanDomains(list, domains, entries);
    printSummary(list.length, protectedCount);
    return;
  }

  // Positional domain arguments
  const domainArgs = args.filter((a) => !a.startsWith('-'));
  if (domainArgs.length === 0) {
    console.log(`${YELLOW}Usage:${RESET}`);
    console.log(`  node bot.js <domain> [domain ...]`);
    console.log(`  node bot.js --file domains.txt`);
    console.log(`  node bot.js --interactive\n`);
    console.log(`${YELLOW}Examples:${RESET}`);
    console.log(`  node bot.js google-analytics.com`);
    console.log(`  node bot.js 33across.com tynt.com example.com\n`);
    process.exit(0);
  }

  const protectedCount = scanDomains(domainArgs, domains, entries);
  printSummary(domainArgs.length, protectedCount);
}

main().catch((err) => {
  console.error(`${RED}Fatal: ${err.message}${RESET}`);
  process.exit(1);
});

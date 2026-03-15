# Radar Bot

A command-line bot that scans domains against Chrome's [IP Protection Masked Domain List (MDL)](../Masked-Domain-List.md) and reports whether each domain is protected.

## Features

- **No external dependencies** — uses only Node.js built-ins.
- **Subdomain resolution** — `sub.tracker.com` is matched if `tracker.com` is on the MDL.
- **URL-tolerant input** — strips `http://` / `https://` prefixes and paths automatically.
- **Rich output** — shows owner name, script-blocking status, and a final summary.
- **Three input modes**: positional arguments, `--file`, and `--interactive`.

## Requirements

- [Node.js](https://nodejs.org/) ≥ 14.0.0
- `Masked-Domain-List.md` present in the parent directory (the default), or a custom path set via the `MDL_PATH` environment variable.

## Usage

```bash
# Scan one or more domains
node bot.js <domain> [domain ...]

# Read domains from a file (one per line)
node bot.js --file domains.txt

# Interactive REPL — type a domain, press Enter, type "exit" to quit
node bot.js --interactive
```

### Examples

```bash
# Single domain
node bot.js google-analytics.com

# Multiple domains at once
node bot.js 33across.com tynt.com example.com

# Subdomains and full URLs are handled automatically
node bot.js sub.33across.com https://tynt.com/path/to/page

# Batch scan from a file
node bot.js --file my-domains.txt

# Use a custom MDL path
MDL_PATH=/path/to/Masked-Domain-List.md node bot.js example.com
```

### Sample output

```
        ___________
       /           \
      /   .  .  .   \
     |  .   [ ]   .  |
      \   .  .  .   /
       \___________/
      I P  P R O T E C T

  📡 Radar Bot — IP Protection MDL Scanner
  Scanning domains against Chrome's Masked Domain List…

  MDL loaded: 4,335 domains from …/Masked-Domain-List.md

  ✔ 33across.com — PROTECTED
      Owner: 33Across
      Script blocking: Not Impacted By Script Blocking
  ✔ tynt.com — PROTECTED
      Owner: 33Across
      Script blocking: Not Impacted By Script Blocking
  ✘ example.com — NOT PROTECTED

─────────────────────────────────────────
  Scanned : 3 domains
  Protected   : 2
  Unprotected : 1
─────────────────────────────────────────
```

## Running the tests

```bash
node test.js
```

The test suite validates MDL parsing, exact-match lookups, subdomain resolution, case-insensitivity, URL normalisation, and a smoke test against the real `Masked-Domain-List.md`.

## How it works

1. **Loads the MDL** — reads `Masked-Domain-List.md` and parses every row of the markdown table into an in-memory `Set` for O(1) lookups.
2. **Normalises each input** — strips protocol prefixes and trailing paths.
3. **Walks up the dot-hierarchy** — checks the full domain, then each successive parent (e.g., `a.b.c` → `b.c`), so that any subdomain of an MDL-listed domain is also detected as protected.
4. **Prints results** — colour-coded ✔/✘ status with owner and script-blocking metadata from the MDL.

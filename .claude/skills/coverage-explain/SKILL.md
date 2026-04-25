---
name: coverage-explain
description: "Use when coverage reports show gaps (reads and explains coverage report data, declares missing coverage strategy)."
allowed-tools:
  - Glob
  - Grep
  - Read
  - Bash(find:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# Skill — coverage-explain

## Scope (strict)

**Read-only advisory.** This skill reads coverage reports and explains the gaps found. It does NOT execute coverage commands, modify thresholds, modify tests, or modify source code.

### You MAY:
- Read coverage report files (`lcov.info` text, `coverage.json`, `htmlcov/index.html`, NYC `.nyc_output/coverage.json`, etc.).
- Treat `.coverage` (coverage.py SQLite DB) as a hint that a JSON/XML report can be generated — do NOT parse the SQLite directly.
- Analyze what lines/branches are uncovered.
- Explain which files have the most gaps.
- Declare a strategy for reaching minimum coverage targets.

### You MUST NOT:
- Execute `npm run test-coverage`, `pytest --cov`, or any coverage tool.
- Modify `coverage.threshold`, `pyproject.toml`, `package.json`, or any config. This skill does not modify thresholds.
- Modify tests or source code.
- Force a specific coverage target (user decides).

## Framing

This is NOT a coverage remediation tool. This is a diagnostic advisor. You read the report and explain what's there, nothing more.

When a coverage report shows a gap:
- Identify the files with the lowest coverage.
- Explain which lines or branches are uncovered (if the report format provides that detail).
- Suggest a MINIMUM viable coverage target based on the repo's current state (e.g., "You have 65% overall; raising to 75% would require testing 3 new files").
- Do NOT rewrite tests or code.

## Steps

1. **Locate coverage report** (Glob + Bash + Read):
   - Search canonical paths: `coverage/lcov.info`, `coverage/lcov-report/lcov.info`, `coverage.json`, `coverage.xml`, `htmlcov/index.html`, `.nyc_output/coverage.json`, `coverage/coverage.json`.
   - `.coverage` (coverage.py SQLite DB) is a hint that a JSON/XML report can be generated — do NOT parse it directly; declare the gap and suggest `coverage json` / `coverage xml`.
   - If user provides a path arg, read that directly (Bash find to verify existence).
   - If no report found, declare: "No coverage report detected in canonical locations. Run your test suite with coverage enabled first (e.g., `npm run test-coverage`, `pytest --cov --cov-report=json`)."
   - Declare which format was found (lcov.info, pytest-cov JSON, NYC, etc.).

2. **Parse report** (Read + analyze):
   - **lcov.info (lcov text format)**: extract file entries (`SF:filename`, `LH:lines_hit`, `LF:lines_found`); compute per-file coverage %.
   - **JSON (pytest-cov, NYC format)**: extract top-level totals + per-file entries; compute %.
   - **HTML directory**: attempt to parse `index.html` for summary or look for embedded JSON data.
   - Declare confidence level: "Full data available" vs "Partial data (summary only)" vs "Heuristic extraction (low confidence)".

3. **Analyze gaps**:
   - **Overall coverage**: extract or compute total (lines_hit / lines_found × 100).
   - **Per-file ranking**: sort all files by coverage % (lowest first).
   - **Severity tiers**:
     - Red (<50%): very low coverage, likely untested.
     - Yellow (50–75%): gaps exist, reasonable targets exist.
     - Green (>75%): mostly covered, refinement phase.
   - For top 3–5 files, calculate: uncovered lines = lines_found - lines_hit.

4. **Declare minimum targets** (advisory, user decides):
   - Current state: "Overall: 65% (X lines covered, Y lines uncovered)."
   - If current < 70%: suggest incremental target (e.g., "Raising to 70–75% would require covering ~X additional lines in the top 3 files below").
   - Do NOT mandate a threshold; frame as "Reasonable next step" or "Minimum baseline".
   - For each red/yellow file, suggest: "File A currently 40%; raising to 60% would add Y lines."

5. **Report format**:
   - **Header**: "Coverage Report Analysis (report from: <source> | timestamp: <if available>)".
   - **Overall stats**: coverage %, total lines/branches.
   - **Top gaps** (top 3–5 files):
     ```
     File | Coverage | Uncovered lines | Suggest to
     -----|----------|-----------------|----------
     src/utils/foo.ts | 45% | 120 | 60% (+60 lines)
     src/api/bar.ts | 52% | 95 | 70% (+40 lines)
     ```
   - **Summary**: "Minimal viable next step: raising overall to 70% requires covering ~X lines across Y files (roughly Z% effort increase)."
   - **Disclaimer**: "This is advisory. User owns coverage strategy. Some lines may be intentionally uncovered (error paths, edge cases, dead code)."

6. **Log** (Bash call):
```bash
.claude/skills/_shared/log-invocation.sh coverage-explain ok
```

## Explicitly out of scope

- Running coverage tools.
- Modifying coverage thresholds or config.
- Writing tests to increase coverage.
- Modifying source code.
- Generating a detailed coverage optimization strategy (that's a separate data-driven task).
- Auditing whether a line SHOULD be covered (subjective).

## Failure modes

- **No coverage report found**: Declare that and suggest running a coverage command.
- **Report format unknown**: Parse as much as you can (heuristics), declare confidence level.
- **Report is stale**: If timestamp shows >1 day old, mention that coverage might not reflect current code.
- **Coverage at 0%**: Report that and suggest running tests first.

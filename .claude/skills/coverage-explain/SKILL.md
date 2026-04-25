---
name: coverage-explain
description: Use when coverage reports show gaps (reads and explains coverage report data, declares missing coverage strategy).
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
- Read coverage report files (lcov.json, .coverage, coverage.json, htmlcov/*, etc.).
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

1. **Locate coverage report** (Glob + Bash):
   - Detect coverage report locations: `coverage/lcov.json`, `.coverage`, `coverage.json`, `coverage.html/`, `htmlcov/`, `.nyc_output/coverage.json`.
   - If user provides a path, read that; otherwise search canonical paths.
   - If no report found, declare the limitation and suggest running coverage first.

2. **Parse report** (Read):
   - If lcov.json format: extract file entries, parse coverage per-file (lines_valid, lines_hit, branches_covered, etc.).
   - If simple JSON: extract top-level coverage metrics (lines, branches, statements, functions).
   - If HTML directory: look for a summary JSON or extract from index.html (heuristic, low confidence).
   - Declare which report format you found and any limitations.

3. **Analyze gaps**:
   - Rank files by coverage % (lowest first).
   - Identify files with <50%, <75%, <90% coverage (thresholds for severity).
   - For each, calculate how many lines/branches are uncovered.

4. **Declare minimum targets**:
   - If repo is currently at 60% overall, suggest raising to 70–75% as a reasonable next step.
   - Do NOT impose a mandate (e.g., "must reach 95%"); user decides.
   - For the top 3 uncovered files, suggest what % would help.

5. **Report**:
   - Current state: overall coverage % (if available).
   - Top uncovered files: sorted by % and gap size.
   - Suggested minimal targets: "Raising the overall threshold to 75% would require covering X additional lines across Y files."
   - No assertions, no directives, no code generation.

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

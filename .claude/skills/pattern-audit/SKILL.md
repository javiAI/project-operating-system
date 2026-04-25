---
name: pattern-audit
description: Use when you want to validate that existing `.claude/patterns/` entries remain consistent with the codebase and flag drift.
allowed-tools:
  - Agent(subagent_type:code-architect)
  - Glob
  - Grep
  - Read
  - Bash(git log:*, git diff:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# pattern-audit — Validate pattern registry consistency

Read-only advisory skill: audit `.claude/patterns/` entries against the codebase to detect drift and inconsistency. Does not modify patterns or code.

## Scope (read-only advisory)

You MAY:
- Read `.claude/patterns/*.md` entries.
- Search the codebase for pattern examples and signal indicators.
- Delegate cross-file analysis to `code-architect` subagent (main prepares context, subagent analyzes, main reports).
- Emit diagnostic reports (drift detected, signal changing, examples stale, etc.).

You MUST NOT:
- Modify `.claude/patterns/` or any other files (advisory-only).
- Auto-apply fixes (user reviews and decides).
- Invoke `/pos:compound` (independent skill, user-driven).

## Drift detection targets

Audit for:
- **Signal drift**: Pattern signal (observable marker) no longer appears in codebase at the expected rate.
- **Stale examples**: References in `.claude/patterns/<name>.md` Examples field point to code that has been refactored away.
- **Inconsistent Rule**: Rule snippet no longer matches actual usage (minor variations that indicate the rule needs versioning or splitting).
- **Obsolete patterns**: No examples found in codebase; pattern is no longer in active use.

## Steps

1. **Load patterns**:
   - Read all `.claude/patterns/*.md` entries.
   - Extract Context, Signal, Rule, Examples, Last observed from each.

2. **Prepare context** (main thread):
   - Collect all patterns + their signals and example file paths.
   - List candidate code files/dirs from Examples.

3. **Delegate to `code-architect`** (if patterns exist):
   - Send all patterns + their signals.
   - Task: "Search the codebase for each pattern's signal. For each pattern, report: (a) signal found ≥2 times (✓), (b) signal drift (changed, found <2 times, no longer found), (c) example files changed/deleted, (d) rule inconsistency. Output: structured drift report per pattern, no code changes."
   - Subagent returns a summary (findings only, no mutations).

4. **Emit diagnostic report**:
   - Header: timestamp, patterns audited count, drift findings count.
   - Per pattern:
     - ✓ Clean: signal found, examples valid, rule consistent.
     - ⚠ Drift: specific findings (e.g., "signal not found in last 5 commits", "Example file /path deleted", "Rule changed").
   - Footer: CTA for user (invoke compound if new patterns, review drift, manually update Last observed if needed).

5. **STOP**. Do NOT:
   - Modify `.claude/patterns/`.
   - Apply fixes to drifted patterns.
   - Refactor code to match patterns.
   - Create PR.

   User reviews the report and decides next action: update patterns, invoke compound for new patterns, or defer.

6. **Log the invocation** (best-effort):

   ```bash
   .claude/skills/_shared/log-invocation.sh pattern-audit ok
   ```

## Failure modes

- `.claude/patterns/` missing or empty → log `status: partial` (nothing to audit).
- `.claude/patterns/` entries malformed (missing Context/Signal/Rule) → log `status: ambiguous`, emit minimal report.
- `git` or codebase read unavailable → log `status: degraded`.
- Subagent returns empty findings → log `status: ok` (audit complete, all clean).

## Explicitly out of scope

- Modifying patterns or code.
- Creating PR (user-gated).
- Enforcing pattern naming/versioning (that's policy).
- Auto-merging pattern proposals from compound (user-reviewed).

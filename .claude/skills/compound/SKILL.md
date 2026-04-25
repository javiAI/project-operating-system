---
name: compound
description: Use when a branch has merged into main and multiple code patterns emerge worth capturing for reuse.
allowed-tools:
  - Agent
  - Glob
  - Grep
  - Read
  - Write
  - Bash(git log:*)
  - Bash(git diff:*)
  - Bash(git merge-base:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# compound — Extract and register reusable code patterns

Extract and register reusable patterns when a merged branch exhibits extractable code or design repetitions. Writer-scoped strict: writes to .claude/patterns/ only — does not touch code, tests, or docs.

## Scope (writer-scoped strict)

You MAY:
- Read the merged diff (`main...HEAD`).
- Delegate deep pattern analysis to `code-architect` subagent via Agent tool (hybrid pattern: main prepares context, subagent analyzes, main writes).
- Create `.claude/patterns/<name>.md` with pattern entries (write-only, strict scope).

You MUST NOT:
- Refactor or modify code (even if patterns are obvious — code lives in prior branches).
- Touch code, tests, or docs outside `.claude/patterns/`.
- Auto-invoke `/pos:pattern-audit` (opt-in after the pattern proposal is reviewed).

## Pattern format

Each `.claude/patterns/*.md` entry declares a reusable pattern with this structure:

```
# Pattern: <name>

## Context
[when this pattern is applicable; preconditions]

## Signal
[observable markers that indicate this pattern should be used]

## Rule
[the actual code snippet, abstraction, or idiom]

## Examples
- Branch/PR: <link or reference>
- Files: <file paths where the pattern appears>

## Last observed
<ISO date>; updated on every audit cycle
```

Mandatory fields: Context, Signal, Rule, Examples. Last observed: timestamped by compound at creation, updated manually by the user or by future pattern-maintenance tools (pattern-audit is read-only advisory; it does not modify patterns).

## Steps

1. **Scope check**: Does the branch diff (per `policy.yaml.lifecycle.post_merge.skills_conditional`) warrant pattern extraction?
   - Trigger: touched paths in `{generator/lib/**, generator/renderers/**, hooks/**, skills/**, templates/**}`.
   - Skip if only docs, only `.claude/patterns/`, or `<MIN_FILES_CHANGED`.
   - Precondition: current branch has merged into main (verify via `git merge-base main HEAD`).

2. **Prepare context** (main thread):
   - Read `git log --oneline main...HEAD` (branch commits).
   - List touched top-level dirs + file count.
   - Collect `.claude/patterns/*.md` existing entries (to avoid duplicates).

3. **Delegate to `code-architect`** via Agent tool (with fallback):
   - Full diff: `git diff main...HEAD`.
   - Existing patterns (so subagent can avoid re-proposing).
   - Explicit task: "identify 1–3 patterns that repeat ≥2 times across the diff and would reduce future duplication. Output: pattern proposals (no code refactoring, no file changes)."
   - Preferred subagent: `code-architect` (pattern extraction via architecture lens).
   - Fallback if unavailable: `general-purpose` with same task (generic analysis acceptable).
   - Subagent returns a summary (not raw code).

4. **Write pattern proposals** (if any):
   - For each pattern from the subagent, create `.claude/patterns/<kebab-slug>.md`.
   - Fill in Context, Signal, Rule (copy from codebase, verbatim), Examples, Last observed (today's ISO date).
   - If a pattern already exists in `.claude/patterns/`, merge (append examples, update Last observed); do NOT overwrite.

5. **STOP**. Do NOT:
   - Create a PR yourself.
   - Invoke `/pos:pattern-audit`.
   - Refactor code outside `.claude/patterns/`.

   Wait for user approval. If patterns are novel, user may review them, invoke pattern-audit, and decide to merge or iterate.

6. **Log the invocation** (best-effort):

   ```bash
   .claude/skills/_shared/log-invocation.sh compound ok
   ```

## Failure modes

- Branch `HEAD` is `main` → no diff; stop. Log `status: partial`.
- Diff empty (no files changed) → no patterns to extract; stop. Log `status: partial`.
- `git merge-base` unavailable → stop; log `status: degraded`.
- Subagent returns empty / trivial suggestions → emit nothing, log `status: partial`.
- Pattern candidate conflicts with existing pattern → flag in pattern comment, user decides merge strategy. Log `status: ok` (attempt made, decision deferred).

## Explicitly out of scope

- Refactoring code (that's a prior branch's job).
- Modifying existing patterns (that's pattern-audit + user decision).
- Creating PR (user-gated).
- Updating MASTER_PLAN, ROADMAP, or docs (not pattern registry duty; docs-sync is separate).

---
name: compress
description: Use when your conversation context is approaching ~120k tokens; suggests which `.claude/logs/*.jsonl` files could be archived or summarized to reclaim context space. Returns analysis only—does not modify files.
allowed-tools:
  - Read
  - Bash(cd:., find:., wc:., head:.)
---

## Framing

This skill helps manage conversation context when logs grow large. It's purely advisory — you decide what to archive, summarize, or discard.

## Scope (strict)

You MAY:
- Read `.claude/logs/*.jsonl` files (use `head`, `wc -l` to sample without loading full content).
- Estimate size/line counts and age of logs.
- Propose which logs are "safe to shrink" (old, already reviewed in memory/docs, verbose but non-critical).
- Recommend action: archive, summarize, or truncate.

You MUST NOT:
- Write to `.claude/logs/` or delete files.
- Modify `.claude/rules/`, `ROADMAP.md`, `HANDOFF.md`, `MASTER_PLAN.md`, `docs/**`.
- Make decisions on behalf of the user about what to keep.
- Suggest compression of operational logs that are part of policy-gated decisions (e.g., `skills.jsonl` if enforcement is active).

## Steps

1. **Sample logs** — list files in `.claude/logs/` with sizes + line counts.
2. **Age check** — read first/last line of each `.jsonl` to infer age range.
3. **Propose candidates** — output in Markdown:
   ```markdown
   ## Compression candidates

   | Log | Lines | Size | Age | Candidate | Reason |
   |-----|-------|------|-----|-----------|--------|
   | skills.jsonl | 48 | 12KB | 3 days | Archive if audit-trail not needed | Rare invocations after E2b kickoff |
   ```

4. **Provide context recovery estimate** — "Archiving X and Y would reclaim ~N tokens and restore conversion space."

5. **Stop** — do NOT act. User decides and executes.

6. **Log invocation** (best-effort):
   ```bash
   .claude/skills/_shared/log-invocation.sh compress ok
   ```

## Explicitly out of scope

- Editing or deleting files.
- Proposing compression of current session's operational logs (only "cold" old logs).
- Modifying docs or changing user decisions.
- Model routing overrides (defaulting to Sonnet).

## Failure modes

- `.claude/logs/` missing → report gracefully; propose step 1 is to create logs if they don't exist yet.
- Log file corrupted or unparseable JSON → skip that file and continue (advisory resilience).

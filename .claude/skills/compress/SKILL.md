---
name: compress
description: Use when your conversation context is approaching ~120k tokens; suggests which `.claude/logs/*.jsonl` files could be archived or summarized to reclaim context space. Read-only advisory—does not modify files.
allowed-tools:
  - Read
  - Bash(ls:*)
  - Bash(find:*)
  - Bash(wc:*)
  - Bash(head:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

## Framing

This skill helps manage conversation context when logs grow large. It's purely **read-only advisory** — you decide what to archive, summarize, or discard.

## Scope (strict)

You MAY:
- List and read `.claude/logs/*.jsonl` files to sample content.
- Estimate size/line counts and rough age of logs.
- Propose which logs are candidates for compression (old, already reviewed, verbose but non-critical).
- Recommend action: archive, summarize, or truncate.

You MUST NOT:
- Write to, edit, or delete any files — not even `.claude/logs/`.
- Modify docs, ROADMAP, HANDOFF, MASTER_PLAN, `.claude/rules/`.
- Make decisions on behalf of the user.
- Suggest archiving operational logs that are actively gated (e.g., `skills.jsonl` if Stop enforcement is live).

## Steps

1. **Enumerate logs** — `ls -lh .claude/logs/*.jsonl` (or `find .claude/logs -name "*.jsonl"`).

2. **Estimate line counts** — `wc -l` per file.

3. **Infer age** — sample first/last line of each file (timestamps in entry `ts` field).

4. **Propose candidates** — output Markdown table:
   ```markdown
   ## Compression candidates

   | Log | Lines | Est. Size | Age range | Action |
   |-----|-------|-----------|-----------|--------|
   | hooks.jsonl | 523 | ~80KB | 4–7 days old | Safe to archive; non-critical operational trace |
   | phase-gates.jsonl | 42 | ~5KB | 1–2 hours old | Keep; recent lifecycle events |
   ```

5. **Estimate context savings** — "Archiving hooks.jsonl + phase-gates-old.jsonl would recover ~100K tokens."

6. **STOP** — do NOT execute. User applies or discards the recommendation.

7. **Log invocation** (best-effort):
   ```bash
   .claude/skills/_shared/log-invocation.sh compress ok
   ```

## Failure modes

- `.claude/logs/` missing → skip gracefully; user likely hasn't run any logs yet.
- Corrupted JSON in a log file → skip that file, continue with others.
- Cannot read file → skip and note in output.

## Explicitly out of scope

- Editing, deleting, or writing any files.
- Proposing compression of **active** operational logs (skills.jsonl if Stop is enforced, phase-gates.jsonl if recent).
- Modifying docs.
- Enforcing compression decisions (user-driven only).

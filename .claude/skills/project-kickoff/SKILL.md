---
name: project-kickoff
description: Use when a session starts, when the user asks to "continúa", "kickoff", "arranca la siguiente rama", or when you need a fast snapshot of repo state before doing branch work. Emits a ≤12-line snapshot (branch, phase, last merge, next branch, warnings). STOPS BEFORE Fase -1 — does not create markers, does not execute branch-plan.
allowed-tools:
  - Read
  - Grep
  - Bash(git log:*)
  - Bash(git status:*)
  - Bash(git rev-parse:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# project-kickoff

Emit a 30-second snapshot so the next action (usually Fase -1 of a new branch) can start from a grounded view of the repo.

Framing: this is an eligibility hint, not a guaranteed auto-trigger. Claude Code decides whether to activate you based on the `description`. Never assume you run on every SessionStart.

## Steps

1. **Gather state** (cheap calls only):
   - `git log --oneline -5`
   - `git status -sb`
   - `git rev-parse --abbrev-ref HEAD`
   - Read `ROADMAP.md` — find the next row marked `⏳` (pending).
   - Read `HANDOFF.md` §1 (Snapshot) and §9 (Próxima rama).

2. **Emit snapshot** — exactly these lines (omit any that don't apply):

   ```text
   Branch: <current>
   Phase:  <derived from branch slug or ROADMAP>
   Last merge: <short sha> <subject>
   Next branch: <slug from ROADMAP ⏳ row>  (status: ⏳ | in-progress | blocked)
   Warnings:
     - <marker missing for next branch, if applicable>
     - <ROADMAP and git log diverge, if applicable>
     - <docs-sync debt from HANDOFF §6b, if any>
   ```

   Keep it ≤12 lines. If there are no warnings, omit the block entirely.

3. **STOP**. Do NOT:
   - create a branch approval marker.
   - execute Fase -1.
   - make edits to any file.

   The user (or a later skill like branch-plan in E1b) will decide what to do with the snapshot.

4. **Log the invocation** (best-effort — last step, never blocks):

   ```bash
   .claude/skills/_shared/log-invocation.sh project-kickoff ok
   ```

   If this step fails for any reason, continue — losing one trace line is acceptable.

## Failure modes

- `git` unavailable → emit the snapshot with `Branch: unknown`, `Phase: unknown`, skip commit/merge lines. Mark `status: degraded` when calling the logger.
- `ROADMAP.md` or `HANDOFF.md` missing → note in Warnings, still emit whatever you have. `status: partial`.
- ROADMAP ⏳ row and `git log` disagree on current branch → emit both in Warnings, don't try to reconcile.

## Explicitly out of scope

- Reading `MASTER_PLAN.md` entirely (cite sections only when needed).
- Reading `docs/ARCHITECTURE.md` (only needed later, during Fase -1).
- Running `branch-plan` or creating approval markers.
- Any write to disk outside the log append in step 4.

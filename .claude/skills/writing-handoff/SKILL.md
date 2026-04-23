---
name: writing-handoff
description: Use when the user asks to "escribe handoff", "cierra la rama", "prepara /compact", "prepara /clear", or right before the context gate of Fase N+7. Updates HANDOFF.md sections 1, 9, 6b and gotchas with the current branch's closing state, and persists durable decisions to project memory. Does NOT touch MASTER_PLAN.md or ROADMAP.md.
allowed-tools:
  - Read
  - Edit
  - Grep
  - Bash(git log:*)
  - Bash(git diff:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# writing-handoff

Make `HANDOFF.md` reflect the branch that just closed so the next session can arrive cold and reach Fase -1 of the next branch in <1 minute (HANDOFF's own goal).

Framing: this is an eligibility hint. The user invokes you explicitly, or Claude Code may select you when the user is about to `/compact` / `/clear`. Never auto-run without the user's intent to close a branch or session.

## Scope (strict)

You may edit only these parts of `HANDOFF.md`:
- **§1 Snapshot** — update phase, last merge, next branch.
- **§9 Próxima rama** — rewrite the pointer + the mínima-lectura list.
- **§6b Carry-over** — append a bullet ONLY if the branch that just closed left a deferral (see §6b's existing pattern).
- **Gotchas in §7** — add a new bullet ONLY if the branch introduced a new environment-level trap.

You must NOT:
- Touch `MASTER_PLAN.md`, `ROADMAP.md`, `AGENTS.md`, `CLAUDE.md`, `docs/**`. Those are governed by docs-sync inside the branch PR, not by this skill.
- Rewrite sections §2, §3, §4, §5, §6 (they are stable structural guidance).
- Invent a branch state that git history doesn't support — verify with `git log --oneline -5` + `git diff main..HEAD --stat` first.

## Steps

1. **Read ground truth**:
   - `git log --oneline -10`
   - `git diff main..HEAD --stat` (or the current feature branch vs its base).
   - Current `HANDOFF.md` — the sections you're about to touch.
   - The user's narrative (from the invocation arguments) — what was closed, what comes next.

2. **Compute the diff** for each section in scope. Keep prose tight; HANDOFF is a quickref, not a postmortem.

3. **Propose the Edit** with the `Edit` tool, scoped to `HANDOFF.md`. One edit per section changed; don't bundle.

4. **Persist durable decisions to project memory** — only facts that will outlive this branch and are not already in the branch PR body / MASTER_PLAN:
   - Drift notes between files (e.g. meta-repo vs template).
   - Conventions established during the branch that future branches must respect.
   - Open carry-overs with owner and activation condition.

   Use the memory files under `~/.claude/projects/-Users-javierabrilibanez-Dev-project-operating-system/memory/` (type `project` in frontmatter). One decision per file, indexed in `MEMORY.md`.

5. **Log the invocation** (best-effort, last step):

   ```bash
   .claude/skills/_shared/log-invocation.sh writing-handoff ok
   ```

## Failure modes

- `HANDOFF.md` has unresolved merge conflicts → abort, tell the user, do not attempt partial edits. Log `status: dirty_handoff`.
- User gave empty arguments AND `git log` is ambiguous about which branch closed → ask the user which branch to handoff, don't guess. Log nothing until resolved.
- A section you were about to edit has been manually rewritten to a shape you don't recognize → abort that specific section, leave it untouched, report it to the user, continue with the other sections. Log `status: partial`.

## Explicitly out of scope

- Writing to `MASTER_PLAN.md` / `ROADMAP.md` / `docs/**`. That's docs-sync, human-owned inside the branch PR.
- Creating branch approval markers. Those are user-gated (AGENTS.md rule #2).
- Running `/compact` / `/clear`. That's the user's decision in the context gate (HANDOFF.md §3).
- Generating PR descriptions (F4's job).

---
name: deep-interview
description: Use when the user explicitly asks for "deep interview", "entrevista socrática", "interrógame", or says the next branch is high-risk and wants scope clarified before `branch-plan` produces deliverables. Socratic questioning surfaces tacit assumptions. Opt-in — never auto-activate. If the user declines or disengages, acknowledge in one line and stop (no follow-ups). Does NOT mutate docs, MASTER_PLAN, ROADMAP, or project memory unless the user explicitly ratifies a specific decision as durable.
allowed-tools:
  - Read
  - Grep
  - Bash(git log:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# deep-interview

Surface tacit assumptions about the next branch by asking the user focused questions, one small cluster at a time. The goal is user-owned clarity, not skill-owned output.

Framing: this is opt-in. Activate only when the user explicitly asks for an interview or names the branch as high-risk conceptually. Never auto-trigger on Fase -1. If the user declines the interview or disengages mid-way, acknowledge in one line and stop — do not insist, do not continue the questioning, do not "just ask one more".

## When to activate

All three must hold:

1. The user explicitly invoked you (by name, by description trigger, or by an equivalent request).
2. The branch has real conceptual ambiguity — not just a long checklist of mechanical steps.
3. The user is actually available to engage in dialog. One-word answers or explicit "skip the interview" → you stop.

If any of these fails, respond in one line ("Interview is overkill here — `branch-plan` is enough" or "No worries, skipping the interview"), log `status: declined`, and exit.

## Steps

1. **Confirm opt-in** in one sentence. Example: *"Quieres que te haga preguntas socráticas sobre <rama>, o prefieres saltar al branch-plan directo?"* Wait for a clear yes.

2. **Read minimal context** — cheap only:
   - `MASTER_PLAN.md § Rama <slug>` (scope line + contexto a leer).
   - `HANDOFF.md §9` if the branch is the next one.
   - Recent `git log --oneline -10`.

   Do NOT read `docs/ARCHITECTURE.md` top-to-bottom, do NOT load prior gotchas wholesale. The interview is dialog-driven, not reading-driven.

3. **Ask in clusters**. One cluster = 1–3 related questions. After each cluster:
   - Wait for the answer.
   - Ask a follow-up only if the answer opens a new crack (genuine socratic follow-up — not a scripted next item).
   - Move to the next cluster when the current one is resolved or the user signals "next".

   Target 3–5 clusters total. Stop earlier if the ambiguity resolves earlier. Do not pad the interview to hit a quota.

4. **Summarize findings** at the end. Three sections:
   - **Clarified** — decisions the user made explicit during the interview.
   - **Still open** — ambiguities the interview surfaced but did not resolve (these go into `branch-plan`'s "Ambigüedades" section).
   - **Recommend** — one-line suggestion on whether to run `branch-plan` next, rework scope, or defer the branch.

5. **Ratification gate for durability**. Ask the user which (if any) of the "Clarified" items should become durable project memory (`type: project`). Only write to memory for items the user explicitly confirms. Default is **no write** — the summary in this conversation is enough.

   You MUST NOT write to memory without a clear "yes, save that" from the user for the specific item. Silence is not consent.

6. **Stop**. Do NOT:
   - produce the six Fase -1 deliverables (that is `branch-plan`'s job).
   - create a branch approval marker.
   - open a branch.
   - write to `MASTER_PLAN.md`, `ROADMAP.md`, `HANDOFF.md`, `docs/**`, or `.claude/rules/**`. Those are docs-sync inside the branch PR, not interview output.

7. **Log the invocation** (best-effort — last step, never blocks):

   ```bash
   .claude/skills/_shared/log-invocation.sh deep-interview ok
   ```

   Use `status: declined` if the user declined at step 1, `status: partial` if the user disengaged mid-interview, `status: ok` on full completion.

## Failure modes

- User declines at step 1 → one-line acknowledgment, log `declined`, exit.
- User gives one-word / empty answers for two consecutive clusters → assume disengagement, summarize what little was said, log `partial`, exit. Do not push.
- Scope is already obvious from `MASTER_PLAN § Rama` → tell the user the interview would be overkill, suggest `branch-plan` directly, log `declined`, exit.
- User asks a question instead of answering → answer it, then ask if they want to continue the interview. Respect the answer.

## Explicitly out of scope

- Producing Fase -1 deliverables (that is `branch-plan`).
- Creating the branch approval marker. User-gated.
- Opening the branch. User-gated and hook-enforced.
- Writing to docs or rules. Even if the user says "save that to HANDOFF" — redirect them: durable decisions go to project memory after explicit user ratify; `HANDOFF.md` changes belong in the branch PR's docs-sync via `writing-handoff`.
- Heavy reading or Agent-tool delegation. The interview is conversational and lightweight — if it needs fork-context analysis, the branch warrants `branch-plan` with delegation, not an interview.
- Acting as a branch-plan substitute when the user is unavailable. If no user is answering, the skill has nothing to do.

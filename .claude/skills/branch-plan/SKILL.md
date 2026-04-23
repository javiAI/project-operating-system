---
name: branch-plan
description: Use when a new branch is about to start and the user asks to "plan la rama", "Fase -1", "propón el plan", or after project-kickoff emitted the snapshot. Reads the branch's context and produces the six Fase -1 deliverables (técnico, conceptual, ambigüedades, alternativas, test plan, docs plan) for user approval. Does NOT create the approval marker. Does NOT open the branch. Does NOT execute Fase -1 changes.
allowed-tools:
  - Read
  - Grep
  - Bash(git log:*)
  - Bash(git diff:*)
  - Bash(git status:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# branch-plan

Produce the six Fase -1 deliverables so the user can approve (or revise) the branch plan before any code is written.

Framing: this is an eligibility hint, not a guaranteed auto-trigger. Claude Code decides whether to activate you based on `description`. Always treat the output as a proposal — the user is the gate.

## Scope (strict)

You MAY:
- Read files cited in the "Contexto a leer" section of `MASTER_PLAN.md § Rama <slug>`.
- Run cheap git introspection (`git log`, `git diff`, `git status`).
- Delegate heavy, cross-file analysis to a subagent via the `Agent` tool (see "Delegation" below).
- Emit the six deliverables in this conversation.

You MUST NOT:
- Create `.claude/branch-approvals/<slug>.approved` (the marker is user-gated, AGENTS.md rule #2).
- Run `git checkout -b`, `git switch -c`, or `git worktree add -b` (branch opening is user-gated; the pre-branch-gate hook would block it anyway without the marker).
- Start implementing Fase 1 (tests), Fase 2 (code), or any later phase — this skill stops at the plan.
- Write to `MASTER_PLAN.md`, `ROADMAP.md`, `HANDOFF.md`, `docs/**`, or any other file on disk. The plan is emitted as conversation, not as artifacts.
- Invoke `deep-interview` for the user. If the branch looks high-risk, surface that in the "Ambigüedades" section and suggest the user invoke `deep-interview` explicitly (opt-in on their side, never automatic).

## Delegation (when reading is heavy)

If producing the plan requires reading ≥3 non-trivial files (e.g., the full `docs/ARCHITECTURE.md` section, multiple prior branches' gotchas, a large rule file, or a significant subtree of `generator/` or `hooks/`), delegate that reading to a subagent instead of loading it into the main context. Use the `Agent` tool with:

- `subagent_type: "Plan"` when you need an independent plan proposal to cross-check against.
- `subagent_type: "code-architect"` when the branch is architectural and you need a second opinion on design patterns.
- `subagent_type: "Explore"` when the task is pure context gathering across many files.

The subagent's summary comes back as a tool result. Fold its conclusions into the deliverables — don't paste its raw output verbatim.

Skip delegation for lightweight branches where the MASTER_PLAN § Rama section already names ≤2 files and the plan is obvious.

## Steps

1. **Identify the target branch**. The user may name it (`feat/e2a-skill-review-simplify`) or point at the next `⏳` row in `ROADMAP.md`. If both are absent, ask — don't guess.

2. **Read the canonical plan for that branch**:
   - `MASTER_PLAN.md § Rama <slug>` — scope + decisiones previas + contexto a leer + criterio de salida.
   - The files listed in "Contexto a leer" of that section — **only those**, cited by range where the section is long.
   - `HANDOFF.md §9 Próxima rama` if the branch is the next one in line.

3. **Gather ground truth** (cheap calls):
   - `git log --oneline -10`
   - `git status -sb`
   - Optional: `git diff main..HEAD --stat` if the branch already has commits (re-planning mid-branch).

4. **If reading is heavy → delegate** (see "Delegation"). Skip this step for lightweight branches.

5. **Emit the six deliverables in order**, with these exact headings:

   1. **Resumen técnico** — files to create/modify, shape changes, test deltas, line-count estimate, invariants touched.
   2. **Resumen conceptual** — what this branch achieves in the arc of the project, what gap it closes, what it deliberately leaves open.
   3. **Ambigüedades reales** — concrete questions whose answers change the plan. Number them (A1, A2, …). Flag any that would warrant `deep-interview` (opt-in, user-invoked).
   4. **Alternativas evaluadas** — for each ambiguity or major choice, list options with a one-line tradeoff and a recommendation.
   5. **Test plan** — RED-first phases, expected net test count, coverage targets, behavior-specific contracts to lock down.
   6. **Docs plan** — which docs need sync in the PR (ROADMAP, HANDOFF, MASTER_PLAN § Rama, rules, architecture), driven by the conditional rules in `policy.yaml.lifecycle.pre_pr.docs_sync_conditional`.

6. **STOP**. Do NOT:
   - create the branch approval marker.
   - run `git checkout -b` / `git switch -c`.
   - start implementation.
   - invoke `deep-interview` for the user.

   Wait for explicit user approval (or revisions). The user decides whether to create the marker and open the branch.

7. **Log the invocation** (best-effort — last step, never blocks):

   ```bash
   .claude/skills/_shared/log-invocation.sh branch-plan ok
   ```

## Failure modes

- `MASTER_PLAN.md § Rama <slug>` missing or empty → emit only the deliverables you can reasonably produce from `HANDOFF.md §9` and `ROADMAP.md`; flag the gap in "Ambigüedades" (A1). Log `status: partial`.
- Ambiguities cannot be resolved from the repo alone → list them in section 3 and stop. Don't invent answers. Log `status: ambiguous`.
- The branch slug conflicts with an existing branch in `git branch -a` → surface it; the user decides whether to resume or rename. Log `status: slug_conflict`.
- `git` unavailable → produce the plan from files only; note the gap. Log `status: degraded`.

## Explicitly out of scope

- Marker creation (`.claude/branch-approvals/<slug>.approved`). User-gated.
- Branch opening (`git checkout -b`). User-gated and hook-enforced.
- Auto-running `deep-interview`. That skill is opt-in — this one can only **suggest** it.
- Any disk write outside the log append in step 7. No draft files, no notes, no `branch-plan-draft.md`. Durability belongs in conversation, PR body, or (for decisions surviving the branch) project memory after user ratification.
- Reading the entire `docs/ARCHITECTURE.md` or `MASTER_PLAN.md` top-to-bottom. Cite by section + line range.

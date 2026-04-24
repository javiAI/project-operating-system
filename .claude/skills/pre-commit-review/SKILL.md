---
name: pre-commit-review
description: Use when the user asks to "revisa la rama", "pre-commit review", "review antes del PR", "chequea el diff", or right before running `gh pr create`. Prepares the review context in the main thread (branch kickoff, scope, applicable invariants), delegates the analysis to the `code-reviewer` subagent via the Agent tool over `git diff main..HEAD`, and folds the subagent summary into prioritized findings. Does NOT rewrite code. Does NOT apply fixes. Does NOT replace `simplify`.
allowed-tools:
  - Read
  - Grep
  - Agent
  - Bash(git log:*)
  - Bash(git diff:*)
  - Bash(git status:*)
  - Bash(git merge-base:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# pre-commit-review

Produce a prioritized review of the current branch's diff (`main..HEAD`) before the user opens a PR with `gh pr create`. Delegate the heavy analysis to the `code-reviewer` subagent; the main thread only prepares context and folds the summary.

Framing: this is an eligibility hint, not a guaranteed auto-trigger. Claude Code decides whether to activate you based on `description`. Output is a review proposal — the user decides which findings to act on.

## Scope (strict)

You MAY:
- Read the kickoff commit and recent branch commits with `git log`.
- Inspect the diff with `git diff main..HEAD`.
- Read `.claude/rules/*.md`, `CLAUDE.md`, and any file cited in the branch's `MASTER_PLAN.md` entry to seed invariants into the review prompt.
- Delegate the analysis to the `code-reviewer` subagent via the Agent tool (see "Delegation" below).
- Emit prioritized findings in this conversation (confidence-filtered, bucketed by severity).

You MUST NOT:
- Rewrite code. The skill does not rewrite code — it produces findings and never edits files.
- Apply fixes. The skill does not apply fixes. Even when a finding has an obvious one-line fix, emit it as a suggestion — do NOT call `Edit` / `Write` / apply a patch.
- Replace `simplify`. They are complementary: `simplify` reduces first, `pre-commit-review` runs after on the already-reduced diff. Running `pre-commit-review` does not obviate `simplify`; running `simplify` does not obviate `pre-commit-review`. This skill does not replace `simplify` and is not a substitute for it.
- Open or describe the PR. `gh pr create` + the PR body are the user's call (and `/pos:pr-description` handles the body in Fase F).
- Create branch approval markers, checkout branches, or otherwise mutate repo state.

## Delegation (hybrid: main prepares context, subagent analyzes)

Main thread stays cheap; heavy analysis goes to the `code-reviewer` subagent via the `Agent` tool:

1. Main gathers context — kickoff commit, branch scope, invariants cited in `.claude/rules/*.md` that touch paths in the diff.
2. Main invokes `Agent(subagent_type="code-reviewer", prompt=...)` with:
   - The prepared context (branch scope + invariants applicable to touched paths).
   - The full diff (`git diff main..HEAD`).
   - Explicit asks: bugs, logic errors, security vulnerabilities, adherence to branch scope, adherence to repo invariants.
3. Subagent runs in its own fork, returns a summary with confidence-filtered findings.
4. Main folds the summary — does NOT paste-through. Prioritizes by severity, attaches `file:line` references, groups by theme if useful.

The string `code-reviewer` here reflects the Claude Code default shipped today. It is hardcoded with a disclaimer: default `subagent_type` names can vary between releases/environments. If the Agent tool's `subagent_type` enum at runtime does NOT include `code-reviewer`, fall back to `general-purpose` with a task prompt that names the same capability (bugs + logic + security + convention adherence). See `.claude/rules/skills.md § Fork / delegación`.

## Steps

1. **Identify the review scope**. Default is the current branch vs `main`:

   ```bash
   git merge-base main HEAD
   git diff main..HEAD --stat
   git log --oneline main..HEAD
   ```

   If the user names a different base, use that. If HEAD is `main` itself, stop — no branch to review.

2. **Prepare the review prompt context** in the main thread:
   - Locate the kickoff commit (commit 1 of the branch) and read its message — it carries scope + decisions.
   - List `.claude/rules/*.md` whose `paths:` frontmatter overlaps the touched paths.
   - Collect applicable invariants from `CLAUDE.md` (regla #3 tests-first, regla #7 patrones antes de abstraer, etc.).
   - Summarize branch scope from `MASTER_PLAN.md § Rama <slug>` if the section exists.

3. **Delegate to `code-reviewer`** via the Agent tool. The prompt must include:
   - Branch name, base, and kickoff scope.
   - Invariants applicable to the touched paths (grep output, not full rule files).
   - The full diff (`git diff main..HEAD`).
   - Explicit asks: "bugs, logic errors, security vulnerabilities, places where the diff leaves the branch scope, and violations of the cited invariants. Group findings by severity (blocker / high / medium / nit). Confidence-filter: omit findings below medium confidence."

   If the runtime Agent tool does NOT list `code-reviewer`, fall back to `general-purpose` with a prompt that names the capability; note the fallback in the user-facing summary.

4. **Fold the subagent summary** into this conversation. Do NOT paste-through:
   - Dedup findings that say the same thing twice.
   - Attach `file:line` references so the user can jump.
   - Reorder by severity + confidence.
   - Add a one-line verdict: `clean to PR` | `findings blocking` | `findings advisory only`.

5. **STOP**. Do NOT:
   - call `Edit` / `Write` to apply any finding.
   - run `gh pr create` or otherwise open the PR.
   - create branch approval markers.

   The user chooses which findings to act on, which to defer, and which to ignore.

6. **Log the invocation** (best-effort — last step, never blocks):

   ```bash
   .claude/skills/_shared/log-invocation.sh pre-commit-review ok
   ```

## Failure modes

- HEAD is `main` / `master` → no branch to review; stop and tell the user. Log `status: partial`.
- `git diff main..HEAD` returns empty → no changes to review; stop. Log `status: partial`.
- `code-reviewer` subagent unavailable at runtime → fall back to `general-purpose` with an equivalent task prompt; note the fallback in the user-facing summary. Log `status: degraded`.
- Subagent returns an empty / unusable summary → report it to the user; do NOT invent findings. Log `status: ambiguous`.

## Explicitly out of scope

- Applying any suggested fix. Findings are output; edits are the user's call (or a separate `simplify` pass for reduction findings).
- Replacing `simplify`. The canonical order is `simplify → pre-commit-review`. Running this skill does not simplify; running `simplify` does not review. This skill does not replace `simplify`.
- Opening the PR (`gh pr create`). User-gated; the `pre-pr-gate` hook enforces docs-sync independently.
- Writing the PR description. `/pos:pr-description` (Fase F) does that.
- Reading the full `docs/ARCHITECTURE.md` or entire rule files top-to-bottom. Cite by grep + range; the subagent receives only the relevant excerpts in the prompt.

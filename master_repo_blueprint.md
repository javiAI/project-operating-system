# Master Repo Blueprint — Workflow Operating System for New Projects

## Purpose

This blueprint turns the working patterns proven in `bnb_guide_builder` into a reusable **project operating system** that can bootstrap new repositories with:

- zero-ambiguity project definition
- deterministic documentation structure
- branch-by-branch implementation planning
- explicit handoff and session restart mechanics
- hook-driven agent workflow
- PR review loops with both architectural and diff-level checks
- token-efficient context loading
- strong human visibility into what is happening and why

This is not a repo-specific plan for tourist rentals. It is a generalized **meta-repo** that produces a project repo with the same discipline, but without domain coupling.

---

## 1. What the current repo already does well

Based on the control files and workflow artefacts in the current repo (`README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/README.md`, `docs/HANDOFF.md`, `prompts/00_START_HERE.md`, `skills/orchestrator/SKILL.md`, plus the phase-driven planning/docs pattern), the current workflow already gets many important things right:

### 1.1 Strong source-of-truth layering
The repo clearly separates:
- repo setup and execution (`README.md`)
- agent operating rules (`CLAUDE.md`, `AGENTS.md`)
- docs entrypoint (`docs/README.md`)
- active plan (`docs/MASTER_PLAN_V2.md`)
- quick session resume (`docs/HANDOFF.md`)
- skills/prompts for execution

This is excellent. It prevents the common failure mode where everything lives in one giant prompt or in unstructured chat context.

### 1.2 Branch-first delivery model
The current system treats work as:
- phase
- branch
- Fase -1 review
- implementation
- validation
- docs updates
- PR review
- post-merge handoff

This is far more reliable than ad-hoc “just implement this feature” prompting.

### 1.3 Context minimization is explicit
The current repo is good at reducing token waste through:
- ordered reading lists
- branch-scoped startup instructions
- `HANDOFF.md`
- roadmap + active-plan split
- not reading the whole plan every time

This is exactly the right direction and should be preserved.

### 1.4 Architecture and execution are tied together
The strongest property of the current system is that it does **not** treat docs as decorative. Docs affect implementation order, PR behavior, validation, and follow-up branch selection.

### 1.5 Human clarity is prioritized
The repo already uses:
- conceptual summaries before implementation
- branch kickoff blocks
- explicit “what changes / why / what is deferred” language
- documented phase completion rules

This should become a hard invariant in the new master repo.

---

## 2. What is still too custom / improvable

### 2.1 Too much project-specific naming and content
The current repo is still tied to one domain, one product shape, one plan history, and one specific design/replatform story.

The master repo must extract the **workflow mechanics** from the **project content**.

### 2.2 The system is not yet bootstrapped from questionnaire → repo
Right now, a lot of the structure exists because it was built iteratively inside one project.

The master repo should generate, from the beginning:
- the right docs
- the right prompts
- the right hooks
- the right phase plan
- the right validations
- the right branch mechanics

### 2.3 There is no formal control plane vs generated repo split
Right now, the current repo is both:
- the product repo
- and the workflow experiment

The master version should split these concerns.

### 2.4 Some workflow behavior is documented but not systematized
Examples:
- when to update CLAUDE.md
- when to create plan-update branches
- how to convert discovered architectural changes into doc changes
- what must happen before opening a PR
- what gets updated post-merge

These should become machine-triggerable or at least template-enforced.

### 2.5 Current prompts still depend too much on remembered context
Even though the repo is disciplined, there is still manual glue:
- “remember to ignore Liora”
- “remember what branch comes next”
- “remember whether invalidation is by sourceFields or by entityType”

The master repo should make this much more deterministic.

---

## 3. The correct generalized model

The correct generalized solution is **not** “make a better CLAUDE.md”.

It is a **two-layer system**:

### Layer A — Meta repo / Control plane
A reusable repository template that knows how to initialize any new project.

### Layer B — Generated project repo
The actual new product repo that receives:
- its own docs
- its own roadmap
- its own prompts
- its own skills
- its own hooks
- its own branch lifecycle

This separation matters.

### Why two layers is better
Because otherwise every product repo becomes both:
- product codebase
- workflow invention sandbox

That is unstable.

---

## 4. What the master repo should do end-to-end

### 4.1 Ask a structured initialization questionnaire
Before any code, the system must force answers to:

#### Product definition
- What is the product?
- Who are the primary users?
- What is the user-visible output?
- What are the primary workflows?
- What must never happen?
- What differentiates this product if done well?

#### Delivery shape
- MVP scope
- phase structure
- critical release gates
- known deferred work
- design ambition level
- regulatory/security sensitivity

#### Technical architecture
- stack
- backend model
- storage model
- hosting/deployment assumptions
- integrations/APIs
- auth model
- testing strategy
- CI expectations

#### Workflow choices
- branch granularity
- PR size preference
- doc strictness level
- agent autonomy level
- review gate strictness
- whether to use formal phase bundles

#### Visual / UX direction
- is there already a design system?
- will there be a future replatform?
- should current branches optimize for architecture over final polish?
- what level of visual discipline is expected during implementation?

#### Team mode
- single operator vs multi-agent vs team
- do humans want conceptual explanations every step?
- how much status verbosity is desired?

### 4.2 Generate the repo skeleton from those answers
The generator should create the initial repository package automatically.

### 4.3 Generate a branch-based implementation roadmap
Not generic “milestones”, but executable branches with:
- purpose
- motivation
- files to create
- files to modify
- tests
- done criteria
- reading list
- docs to update
- tools/skills to use
- defer list

### 4.4 Generate the operating docs
Not as stubs. As usable, aligned files.

### 4.5 Generate hook behavior
The repo should remind or enforce:
- pre-branch kickoff
- pre-commit review
- pre-PR simplify/review
- post-merge doc updates
- handoff refresh

### 4.6 Generate prompts for agents
There should be ready-to-use prompts for:
- ChatGPT planning/orchestration
- Claude Code implementation
- PR review
- plan-update branches
- branch kickoff
- post-merge resume

---

## 5. Recommended structure of the master repo

```text
project-os/
├─ README.md
├─ AGENTS.md
├─ CLAUDE.md
├─ package.json / pyproject.toml / tooling as needed
├─ bootstrap/
│  ├─ questionnaire/
│  │  ├─ product.yaml
│  │  ├─ architecture.yaml
│  │  ├─ workflow.yaml
│  │  └─ ux.yaml
│  ├─ schemas/
│  │  ├─ init-project.schema.json
│  │  ├─ roadmap.schema.json
│  │  └─ docs.schema.json
│  ├─ generators/
│  │  ├─ init_project.py
│  │  ├─ render_docs.py
│  │  ├─ render_prompts.py
│  │  ├─ render_skills.py
│  │  ├─ render_hooks.py
│  │  └─ render_plan.py
│  └─ templates/
│     ├─ root/
│     ├─ docs/
│     ├─ prompts/
│     ├─ skills/
│     ├─ hooks/
│     ├─ checks/
│     └─ .github/
├─ templates/
│  ├─ docs/
│  ├─ prompts/
│  ├─ skills/
│  ├─ hooks/
│  ├─ checks/
│  └─ .claude/
├─ docs/
│  ├─ README.md
│  ├─ MASTER_WORKFLOW_SPEC.md
│  ├─ WORKFLOW_ARCHITECTURE.md
│  ├─ FILE_GENERATION_RULES.md
│  ├─ PHASE_PLANNING_RULES.md
│  ├─ HOOKS_AND_AUTOMATIONS.md
│  ├─ TOKEN_EFFICIENCY_RULES.md
│  ├─ HUMAN_EXPLAINABILITY_RULES.md
│  └─ REVIEW_SYSTEM.md
├─ prompts/
│  ├─ 00_INIT_PROJECT.md
│  ├─ 01_START_BRANCH.md
│  ├─ 02_PLAN_UPDATE.md
│  ├─ 03_REVIEW_PR.md
│  ├─ 04_POST_MERGE.md
│  └─ 05_REPO_AUDIT.md
├─ skills/
│  ├─ orchestrator/
│  ├─ planning/
│  ├─ implementation/
│  ├─ review/
│  ├─ docs-sync/
│  └─ release/
├─ hooks/
│  ├─ pre-branch.sh
│  ├─ pre-commit.sh
│  ├─ pre-pr.sh
│  ├─ post-merge.sh
│  └─ sync-handoff.sh
├─ checks/
│  ├─ validate_docs_sync.py
│  ├─ validate_plan_integrity.py
│  ├─ validate_prompt_refs.py
│  ├─ validate_hooks_config.py
│  └─ validate_repo_bootstrap.py
└─ .github/
   ├─ workflows/
   ├─ pull_request_template.md
   ├─ ISSUE_TEMPLATE/
   └─ instructions/
```

---

## 6. What every generated project repo should contain

For each new project, the generator should create this minimum set:

### Root control files
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.gitignore`
- `.editorconfig`
- `.gitattributes`

### Docs
- `docs/README.md`
- `docs/ARCHITECTURE_OVERVIEW.md`
- `docs/DATA_MODEL.md`
- `docs/API_ROUTES.md`
- `docs/SECURITY_AND_AUDIT.md`
- `docs/QA_AND_RELEASE.md`
- `docs/ROADMAP.md`
- `docs/MASTER_PLAN.md` or `MASTER_PLAN_V2.md`
- `docs/HANDOFF.md`
- `docs/FUTURE.md`
- `docs/FEATURES/...` generated from chosen modules

### Agent assets
- `prompts/00_START_HERE.md`
- `prompts/branch-kickoff.md`
- `prompts/plan-update.md`
- `prompts/review-pr.md`
- `prompts/post-merge.md`
- `skills/orchestrator/SKILL.md`
- `skills/review/SKILL.md`
- `skills/docs-sync/SKILL.md`
- `skills/phase-active/...`

### Automation
- `.claude/` files
- `hooks/`
- `checks/`
- `.github/workflows/`
- `.github/pull_request_template.md`

---

## 7. The initialization questionnaire the master repo should ask

The generator should not rely on freeform chat only. It should combine:
- structured form
- explanatory prompts
- validation

## 7.1 Core questionnaire

### A. Product
1. Project name
2. One-sentence product definition
3. End-state vision (what “finished” looks like)
4. Primary users
5. Core workflows
6. Differentiators
7. Absolute no-go failures

### B. Scope and phasing
8. MVP boundary
9. Likely major phases
10. What can be deferred safely
11. What must be reliable from day 1

### C. Architecture
12. Frontend stack
13. Backend stack
14. Database/storage
15. Auth model
16. Deployment environment
17. External providers
18. Search/RAG/AI expectations
19. Media/file handling expectations
20. CI/CD expectations

### D. UX / design
21. Existing design system or none
22. Design ambition level
23. Is there a future replatform expected?
24. Accessibility target
25. Locale/unit requirements

### E. Workflow policy
26. Branch granularity
27. Doc strictness
28. PR strictness
29. Test strictness
30. Agent autonomy level
31. Whether to prefer fewer large docs vs more modular docs
32. Whether human wants conceptual summaries at every stage
33. How terse or verbose status communication should be

### F. Security / compliance
34. Sensitive data classes
35. Visibility model
36. PII handling rules
37. Audit/logging needs

### G. Meta behavior
38. Should plan changes require separate plan-update branches?
39. Should post-merge always refresh HANDOFF and ROADMAP?
40. Should every branch have Fase -1 kickoff?

---

## 8. What the generator should output from the questionnaire

## 8.1 A project profile file
`project_profile.yaml`

This becomes the machine-readable source of truth for generation.

It should include:
- product summary
- stack
- workflow policy
- phase strategy
- doc set selection
- security model
- design/replatform settings
- output verbosity policy

## 8.2 A docs map
A generated file such as `docs/_generated/doc_manifest.json` should say:
- which docs were generated
- why they exist
- which questionnaire fields created them
- which are editable
- which are generated

## 8.3 A branch map
A generated `docs/MASTER_PLAN.md` that already contains:
- phase order
- branch IDs
- done criteria
- docs to update per branch
- tool usage per branch

## 8.4 A hook policy file
Something like `hooks/hook_policy.yaml` that centralizes:
- which hooks are active
- whether they block or only remind
- what they validate

---

## 9. The ideal branch workflow in the generated project repo

Every branch should follow this exact loop:

### 9.1 Before creating branch
- read `docs/HANDOFF.md`
- read branch section in `docs/MASTER_PLAN.md`
- execute Fase -1
- clarify ambiguities
- get approval
- create branch

### 9.2 During implementation
- work only inside branch scope
- maintain docs alignment if contract changes
- use subagents in parallel when helpful
- keep human informed conceptually, not just technically

### 9.3 Before commit
- run pre-commit review skill/hook
- summarize what changed and why
- confirm no drift from branch scope

### 9.4 Before PR
- run simplify
- update docs listed in branch plan
- update ROADMAP status
- update HANDOFF “next branch” if needed
- run checks/tests

### 9.5 During PR review
- classify comments by:
  - blocker
  - important
  - optional
  - wrong / discardable
- maintain explicit triage log

### 9.6 After merge
- refresh ROADMAP
- refresh HANDOFF
- refresh CLAUDE.md only if reusable pattern was learned
- mark next branch
- emit kickoff block for next session

---

## 10. Hooks the master repo should generate

## 10.1 pre-branch
Purpose:
- stop branch creation before Fase -1 is approved
- ensure current branch clean
- ensure roadmap/handoff not stale

Checks:
- working tree clean or acknowledged
- previous PR merged/closed
- `docs/HANDOFF.md` updated recently
- approval marker exists

## 10.2 pre-commit
Purpose:
- remind to run targeted review
- require minimal status summary
- prevent stealth doc drift if files touched require docs sync

Checks:
- changed files vs docs obligations
- if schema/config/plan files changed, require docs sync acknowledgment
- if PR-comment triage file exists and unresolved blockers remain, warn/block

## 10.3 pre-pr
Purpose:
- ensure branch is ready

Checks:
- simplify run marker exists
- tests run marker exists
- roadmap updated if branch completes phase item
- handoff updated if merge would change next step
- no branch naming drift

## 10.4 post-merge
Purpose:
- standardize handoff refresh

Actions/reminders:
- mark roadmap status
- set next branch in handoff
- optionally revise CLAUDE.md reusable patterns

---

## 11. Skills the master repo should provide

## 11.1 Orchestrator skill
Role:
- decide what to read
- decide what phase comes next
- enforce scope discipline

## 11.2 Planning skill
Role:
- generate or revise branch plans
- enforce file-by-file scope
- surface ambiguities before code

## 11.3 Implementation skill
Role:
- implement only approved branch scope
- update required docs
- run checks

## 11.4 Review skill
Role:
- classify PR comments
- decide what blocks merge
- distinguish local diff issues from architecture issues

## 11.5 Docs-sync skill
Role:
- reconcile code ↔ docs ↔ plan
- update roadmap/handoff/future

## 11.6 Release skill
Role:
- gather checks
- produce release report
- verify gates

---

## 12. Human visibility rules (very important)

The new system should explain what is happening at two levels every time:

### Conceptual layer
- what stage we are in
- why this stage exists
- what changes in the project if it succeeds
- what remains deferred

### Technical layer
- what files are being changed
- what contract is being changed
- what risks exist
- what tests validate it

This is critical.

The human should never feel:
- “things are happening but I don’t know why”
- “the agent is changing docs randomly”
- “the branch moved the plan silently”

---

## 13. Token-efficiency rules for the master repo

This is one of the most important parts.

### 13.1 Never load everything by default
Use:
- README
- AGENTS/CLAUDE
- docs index
- handoff
- active branch section only

### 13.2 Keep long plans segmented by branch
A plan should be navigable branch by branch, never requiring full-file reading on every session.

### 13.3 Make docs role-specific
Examples:
- `HANDOFF.md` = shortest operational resume
- `ROADMAP.md` = current status only
- `MASTER_PLAN.md` = execution contract
- `ARCHITECTURE_OVERVIEW.md` = persistent system truths
- `FUTURE.md` = deferred work only

### 13.4 Split generated and human-edited docs
Mark which docs are:
- generated
- user-maintained
- agent-maintained
- branch-updated

### 13.5 Use stable reusable prompt shells
Instead of re-writing giant prompts each time, generate:
- kickoff prompt shell
- review prompt shell
- post-merge prompt shell
with project variables filled in

### 13.6 Use handoff docs, not chat memory, as primary persistence
Chat memory is helpful, but repo files must be the canonical resume mechanism.

---

## 14. What should become non-repo-specific from the current system

The following patterns should be preserved and generalized:

### Keep
- explicit order of reading
- branch kickoff ritual
- Fase -1 gate
- docs update obligations per branch
- handoff/roadmap split
- post-merge next-step clarity
- skills by role
- validate-before-PR discipline
- architectural review + diff-level review combination

### Remove repo-specific coupling
- phase IDs tied to one product domain
- references to one design track like Liora
- product-specific docs names where generic names would do
- hardcoded domain taxonomies in startup docs
- assumptions about Next.js/Prisma unless chosen in questionnaire

---

## 15. Proposed generated docs set for every new project

This is the recommended minimum.

### Root
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`

### docs/
- `docs/README.md`
- `docs/ARCHITECTURE_OVERVIEW.md`
- `docs/DATA_MODEL.md`
- `docs/API_ROUTES.md`
- `docs/SECURITY_AND_AUDIT.md`
- `docs/QA_AND_RELEASE.md`
- `docs/ROADMAP.md`
- `docs/MASTER_PLAN.md`
- `docs/HANDOFF.md`
- `docs/FUTURE.md`
- `docs/FEATURES/` per feature family
- `docs/research/` only if formal research/spec docs exist

### prompts/
- `prompts/00_START_HERE.md`
- `prompts/BRANCH_KICKOFF.md`
- `prompts/PLAN_UPDATE.md`
- `prompts/PR_REVIEW.md`
- `prompts/POST_MERGE.md`
- `prompts/REPO_AUDIT.md`

### skills/
- `skills/orchestrator/SKILL.md`
- `skills/planning/SKILL.md`
- `skills/implementation/SKILL.md`
- `skills/review/SKILL.md`
- `skills/docs-sync/SKILL.md`

### checks/
- validators for plan, docs, references, phase completeness, hook policy

### hooks/
- pre-branch
- pre-commit
- pre-pr
- post-merge

---

## 16. Recommended implementation strategy for building this meta-repo

Do not try to build the final system in one go.

### Phase A — Define the control plane
Build:
- questionnaire schema
- project profile schema
- repo generation rules
- doc generation rules
- prompt generation rules

### Phase B — Generate one minimal project template
Generate:
- README
- AGENTS
- CLAUDE
- docs index
- architecture/data/security/QA docs
- roadmap/master plan/handoff/future
- one branch kickoff prompt
- one review prompt
- orchestrator skill

### Phase C — Add hooks and checks
Add:
- branch lifecycle enforcement
- doc sync checks
- roadmap/handoff sync checks

### Phase D — Add phase plan generator
Take questionnaire answers and generate:
- feature phases
- branch list
- file scopes
- docs obligations

### Phase E — Add review loop assets
Generate:
- PR template
- review triage template
- plan-update branch template

### Phase F — Harden token efficiency
Add:
- doc manifests
- generated-vs-manual markers
- compact startup docs

---

## 17. What the “ideal” repo should feel like in practice

When a new project starts, the workflow should feel like this:

1. Answer questionnaire
2. Generator creates repo skeleton
3. Human reads short generated overview and approves
4. Agent begins with `00_START_HERE`
5. First branch kickoff is deterministic
6. Every branch explains conceptually what is happening
7. Every PR has aligned docs and reviews
8. Every merge leaves the repo ready for the next branch
9. Starting a new session is cheap
10. There is never ambiguity about:
   - what is active
   - what is deferred
   - what the next step is
   - what docs matter right now

That is the target.

---

## 18. Prompt for Claude Code (complete)

```text
You are helping design and build a reusable “project operating system” repository.

Goal:
Create a master repository that can bootstrap new software projects from the beginning with:
- zero ambiguity
- strong planning
- deterministic docs structure
- branch-by-branch execution
- hooks and checks
- reusable prompts and skills
- token-efficient agent workflow
- explicit conceptual explanations for the human at every stage

This is NOT a product repo. It is a meta-repo that generates project repos.

Your job in this session:
1. Analyze the current workflow patterns from the reference repo.
2. Extract the reusable mechanics from the repo-specific content.
3. Design the ideal generalized repo structure.
4. Define the questionnaire that initializes a new project.
5. Define the generated file set.
6. Define hook behavior and validation behavior.
7. Define how branch lifecycle works from kickoff to merge.
8. Define how docs stay synchronized.
9. Define how token efficiency is preserved.
10. Produce implementation-ready artefacts for the meta-repo.

Important constraints:
- prioritize determinism over cleverness
- prefer generated structure over remembered context
- optimize for long projects with many branches and many sessions
- make the system understandable to a human operator
- always explain both conceptually and technically what is happening
- do not hardcode domain assumptions from the reference repo unless they are generalized into configuration
- generated docs must distinguish between: generated / manually maintained / branch-updated
- prompts, hooks, checks, docs, and skills must work together as one system
- plan changes discovered during implementation must have a formal path, not silent drift

Deliverables:
- ideal repo tree for the meta-repo
- generation model (questionnaire -> profile -> files)
- core docs inventory and responsibility of each file
- hooks inventory and when each one runs
- checks inventory and what each one validates
- reusable prompt set for generated project repos
- reusable skills set for generated project repos
- lifecycle diagram for branch execution
- rules for post-merge repo state
- strategy for minimizing token usage in long-running projects
- migration plan from the current custom workflow to the generalized master repo

Work in this order:
1. Diagnose the current workflow strengths and weaknesses.
2. Propose the generalized architecture.
3. Propose the generated repo structure.
4. Propose the initialization questionnaire.
5. Propose hooks/checks/prompts/skills.
6. Propose the build plan for the meta-repo itself.

Do not start coding immediately.
First produce a very detailed architecture and execution plan.
Then wait for approval before converting that plan into repo files.
```

---

## 19. Prompt for a new ChatGPT session (complete)

```text
I want you to act as the architect and workflow designer for a reusable “project operating system” repository.

Context:
I have been using a very strong workflow inside a long-running product repository:
- branches with explicit planning
- branch-by-branch execution
- roadmap + handoff + future docs
- agent operating rules (`CLAUDE.md`, `AGENTS.md`)
- prompts and skills per phase
- pre-commit / pre-PR / post-merge discipline
- PR reviews with both architectural and line-level analysis
- iterative refinement using both ChatGPT and Claude Code

This workflow works very well, but it is too custom to that product.

Now I want to create a NEW MASTER REPOSITORY that I can reuse every time I start a new project.

The master repository should, from a structured project questionnaire, generate:
- a clean repo operating system
- the right docs
- the right prompts
- the right skills
- the right hooks
- the right validation checks
- the right roadmap / master plan / handoff structure
- a branch workflow that removes ambiguity from the start

Main goals:
- automate as much as possible
- eliminate ambiguity
- keep docs, plan, prompts, hooks, and reviews aligned
- preserve token efficiency across long projects and many sessions
- ensure the human always understands conceptually what is happening, not only technically
- support parallel agents when appropriate
- make repo state always resumable after `/clear` or a fresh session

What I want from you in this session:
1. Analyze the current workflow pattern conceptually.
2. Extract what should become generic and reusable.
3. Design the ideal master repo structure.
4. Specify what files should be generated into every new project repo.
5. Define the initialization questionnaire for a new project.
6. Define the branch lifecycle from kickoff to merge.
7. Define hook behavior and checks.
8. Define prompt architecture for both Claude Code and ChatGPT.
9. Define the rules for token efficiency and human explainability.
10. Produce a super-detailed implementation plan for the master repo itself.

Constraints:
- do not give me vague advice
- be explicit, systematic, and operational
- separate what belongs to the meta-repo vs what belongs to each generated project repo
- show how this becomes non-repo-specific
- preserve the strongest ideas from the current workflow but generalize them properly
- prioritize long-term maintainability and low ambiguity

Output structure required:
1. Diagnosis of current workflow
2. What must be preserved
3. What must be generalized
4. Meta-repo architecture
5. Generated-project architecture
6. Questionnaire design
7. Hooks/checks/prompts/skills design
8. Branch lifecycle design
9. Token-efficiency rules
10. Human explainability rules
11. Detailed implementation roadmap for building the meta-repo
12. Risks / tradeoffs / things to avoid

Do not optimize for brevity.
Optimize for clarity, completeness, and operational usefulness.
```

---

## 20. Final recommendation

Do not build this as “some docs templates”.
Build it as a real **workflow compiler**:

**Questionnaire → project profile → generated repo operating system → deterministic branch execution**.

That is the right abstraction.

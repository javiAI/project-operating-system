"""Contract tests for the Claude Code Skill primitive used by pos (E1 + E2a).

Scope:
  - Frontmatter shape (official primitive: name + description + allowed-tools).
  - No invented fields (no skill.json, no `context:` / `model:` / `agent:` /
    `effort:` — those were speculative in docs/ARCHITECTURE.md §5 pre-E1a).
  - Each SKILL.md references the shared logger `.claude/skills/_shared/log-invocation.sh`
    so invocations surface in `.claude/logs/skills.jsonl` (best-effort — the
    LLM may skip the last step; the system degrades to losing that one trace).
  - `name` in the frontmatter matches the directory name (convention).
  - description framed as "Use when …" (selection hint, not guaranteed trigger).

Integration with stop-policy-check + skills_allowed lives in
`hooks/tests/test_skills_log_contract.py`. This file is pure primitive contract.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

# Skill slugs delivered through Fase E so far. Constant is contract-bound
# (must match `policy.yaml.skills_allowed` exactly), not era-bound — it was
# renamed from `E1_SKILLS_KNOWN` to `ALLOWED_SKILLS` in E2a once the allowlist
# crossed a phase boundary. Adding a skill = extending this list +
# `policy.yaml.skills_allowed` in the same branch; the suite's 11 parametrized
# contract tests cover it automatically.
#
# Delivered:
#   E1a — project-kickoff, writing-handoff
#   E1b — branch-plan, deep-interview
#   E2a — pre-commit-review, simplify
#   E2b — compress, audit-plugin
ALLOWED_SKILLS = [
    "project-kickoff",
    "writing-handoff",
    "branch-plan",
    "deep-interview",
    "pre-commit-review",
    "simplify",
    "compress",
    "audit-plugin",
]

# Officially supported SKILL.md frontmatter fields in Claude Code.
# Extending this set requires citing an official source — see feedback memory
# "Skill primitive stays minimal" and docs/ARCHITECTURE.md §5.
ALLOWED_FRONTMATTER_KEYS = {"name", "description", "allowed-tools"}
REQUIRED_FRONTMATTER_KEYS = {"name", "description"}


def read_skill(slug: str) -> tuple[dict, str]:
    """Return `(frontmatter, body)` for `.claude/skills/<slug>/SKILL.md`.

    Raises `AssertionError` with a clear reason if the shape is wrong — this
    is a contract test, explicit failure is more useful than a KeyError.
    """
    path = SKILLS_DIR / slug / "SKILL.md"
    assert path.exists(), f"SKILL.md missing for skill '{slug}': {path}"
    raw = path.read_text(encoding="utf-8")
    # Split on the YAML frontmatter delimiters (---\n ... \n---\n).
    parts = raw.split("---\n", 2)
    assert len(parts) >= 3 and parts[0] == "", (
        f"SKILL.md for '{slug}' does not start with '---\\n<yaml>\\n---\\n' "
        f"frontmatter (got: {parts[0]!r}...)"
    )
    frontmatter = yaml.safe_load(parts[1]) or {}
    body = parts[2]
    assert isinstance(frontmatter, dict), (
        f"SKILL.md frontmatter for '{slug}' must parse as a YAML mapping, "
        f"got {type(frontmatter).__name__}"
    )
    return frontmatter, body


# ────────────────────────────────────────────────────────────────────────────
# Structure: file exists and parses as frontmatter + body
# ────────────────────────────────────────────────────────────────────────────


class TestStructure:
    @pytest.mark.parametrize("slug", ALLOWED_SKILLS)
    def test_skill_dir_exists(self, slug: str):
        assert (SKILLS_DIR / slug).is_dir()

    @pytest.mark.parametrize("slug", ALLOWED_SKILLS)
    def test_skill_md_exists(self, slug: str):
        assert (SKILLS_DIR / slug / "SKILL.md").is_file()

    @pytest.mark.parametrize("slug", ALLOWED_SKILLS)
    def test_skill_md_parses(self, slug: str):
        fm, body = read_skill(slug)
        assert fm and body

    @pytest.mark.parametrize("slug", ALLOWED_SKILLS)
    def test_no_skill_json(self, slug: str):
        """skill.json is not part of the official primitive. Don't emit it."""
        assert not (SKILLS_DIR / slug / "skill.json").exists()


# ────────────────────────────────────────────────────────────────────────────
# Frontmatter: minimal, no invented fields
# ────────────────────────────────────────────────────────────────────────────


class TestFrontmatter:
    @pytest.mark.parametrize("slug", ALLOWED_SKILLS)
    def test_required_keys_present(self, slug: str):
        fm, _ = read_skill(slug)
        missing = REQUIRED_FRONTMATTER_KEYS - set(fm)
        assert not missing, (
            f"Skill '{slug}' frontmatter missing required keys: {missing}"
        )

    @pytest.mark.parametrize("slug", ALLOWED_SKILLS)
    def test_no_invented_fields(self, slug: str):
        """Only the official three fields are allowed. Adding more requires a
        citation (see feedback memory 'Skill primitive stays minimal')."""
        fm, _ = read_skill(slug)
        extra = set(fm) - ALLOWED_FRONTMATTER_KEYS
        assert not extra, (
            f"Skill '{slug}' frontmatter has non-official fields: {extra}. "
            "Remove them or justify with an official Claude Code doc citation."
        )

    @pytest.mark.parametrize("slug", ALLOWED_SKILLS)
    def test_name_matches_dir(self, slug: str):
        fm, _ = read_skill(slug)
        assert fm["name"] == slug, (
            f"frontmatter name={fm['name']!r} does not match dir name={slug!r}"
        )

    @pytest.mark.parametrize("slug", ALLOWED_SKILLS)
    def test_description_is_use_when_shape(self, slug: str):
        """description is a selection hint for the model, not a guaranteed
        trigger. Frame as 'Use when …' so the model treats it as eligibility,
        not auto-activation."""
        fm, _ = read_skill(slug)
        desc = fm["description"]
        assert isinstance(desc, str) and desc.strip()
        # Case-insensitive because the frontmatter wording is editable.
        assert desc.lower().startswith("use when"), (
            f"Skill '{slug}' description should start with 'Use when …' "
            f"(frame as selection hint, not auto-trigger). Got: {desc!r}"
        )

    @pytest.mark.parametrize("slug", ALLOWED_SKILLS)
    def test_allowed_tools_shape(self, slug: str):
        """`allowed-tools` is optional. If present, it must be a list of
        non-empty strings — no strings with wildcards alone, no nested shapes."""
        fm, _ = read_skill(slug)
        if "allowed-tools" not in fm:
            return
        tools = fm["allowed-tools"]
        assert isinstance(tools, list), (
            f"Skill '{slug}' allowed-tools must be a list, got "
            f"{type(tools).__name__}"
        )
        for t in tools:
            assert isinstance(t, str) and t.strip(), (
                f"Skill '{slug}' allowed-tools must contain non-empty strings; "
                f"got entry {t!r}"
            )

    @pytest.mark.parametrize("slug", ALLOWED_SKILLS)
    def test_name_has_no_pos_prefix(self, slug: str):
        """No `pos:` prefix in skill names. The plugin marketplace namespace
        (if ever packaged) is applied by the marketplace, not by us."""
        fm, _ = read_skill(slug)
        assert not fm["name"].startswith("pos:"), (
            f"Skill name {fm['name']!r} must not carry the 'pos:' prefix."
        )


# ────────────────────────────────────────────────────────────────────────────
# Body: references the shared logger
# ────────────────────────────────────────────────────────────────────────────


class TestBody:
    @pytest.mark.parametrize("slug", ALLOWED_SKILLS)
    def test_body_references_shared_logger(self, slug: str):
        """Skills must emit a log entry to .claude/logs/skills.jsonl via the
        shared helper. Best-effort: the model can skip it in a rare invocation
        and the system just loses that one trace — never breaks."""
        _, body = read_skill(slug)
        assert ".claude/skills/_shared/log-invocation.sh" in body, (
            f"Skill '{slug}' body should reference "
            "`.claude/skills/_shared/log-invocation.sh` so invocations surface "
            "in skills.jsonl."
        )


# ────────────────────────────────────────────────────────────────────────────
# Shared logger presence (the helper itself)
# ────────────────────────────────────────────────────────────────────────────


class TestSharedLogger:
    def test_logger_exists(self):
        path = SKILLS_DIR / "_shared" / "log-invocation.sh"
        assert path.is_file(), f"shared logger missing: {path}"

    def test_logger_is_executable(self):
        import os
        path = SKILLS_DIR / "_shared" / "log-invocation.sh"
        assert os.access(path, os.X_OK), f"shared logger not executable: {path}"


# ────────────────────────────────────────────────────────────────────────────
# Behavior-specific contracts (E1b — branch-plan + deep-interview)
#
# These lock down scope decisions taken in Fase -1 of E1b so later edits
# don't silently drift the body away from the contract (e.g., branch-plan
# suddenly creating markers, or deep-interview writing to memory without
# user ratification).
# ────────────────────────────────────────────────────────────────────────────


class TestBranchPlanBehavior:
    def test_body_mentions_fase_minus_one_deliverables(self):
        """The 6 canonical Fase -1 outputs must all be named in the body so
        invocations produce the full package (technical + conceptual +
        ambiguities + alternatives + test plan + docs plan)."""
        _, body = read_skill("branch-plan")
        low = body.lower()
        for token in (
            "técnico",
            "conceptual",
            "ambig",
            "alternativ",
            "test plan",
            "docs plan",
        ):
            assert token in low, (
                f"branch-plan body should mention '{token}' — one of the "
                "six Fase -1 deliverables the skill must produce."
            )

    def test_body_disclaims_marker_and_branch_creation(self):
        """branch-plan must explicitly state it does NOT create the branch
        approval marker and does NOT open the branch — those are user-gated
        (AGENTS.md rule #2). Mirrors project-kickoff's STOP-before-Fase-1."""
        _, body = read_skill("branch-plan")
        low = body.lower()
        assert "marker" in low, (
            "branch-plan body must mention 'marker' so its scope (not "
            "creating the approval marker) is unambiguous."
        )
        disclaim_tokens = (
            "does not",
            "do not",
            "no crea",
            "no abre",
            "never ",
            "not create",
            "not execute",
        )
        assert any(tok in low for tok in disclaim_tokens), (
            "branch-plan body must disclaim marker creation, branch opening, "
            "or Fase -1 auto-execution (use 'does not', 'no crea', etc.)."
        )

    def test_body_contains_stop_signal(self):
        """Mirror project-kickoff: an explicit 'STOP' uppercase boundary
        marker signals where the skill hands control back to the user."""
        _, body = read_skill("branch-plan")
        assert "STOP" in body, (
            "branch-plan body should contain explicit 'STOP' (uppercase) "
            "mirroring project-kickoff's boundary signal."
        )


class TestDeepInterviewBehavior:
    def test_body_frames_socratic(self):
        _, body = read_skill("deep-interview")
        low = body.lower()
        assert "socratic" in low or "socrátic" in low, (
            "deep-interview body should frame itself as socratic "
            "questioning so the model treats the skill as a clarifier, "
            "not a solver."
        )

    def test_body_is_opt_in(self):
        """deep-interview must not auto-run — the user has to ask for it.
        If they decline, the skill does not insist."""
        _, body = read_skill("deep-interview")
        low = body.lower()
        opt_in_tokens = (
            "opt-in",
            "opt in",
            "user invokes",
            "user-invoked",
            "only when",
            "user explicitly",
            "explícitamente",
        )
        assert any(tok in low for tok in opt_in_tokens), (
            "deep-interview body must mark itself opt-in (user-invoked), "
            "so the model doesn't auto-activate on every Fase -1."
        )

    def test_body_guards_against_silent_mutation(self):
        """Durable outputs (docs, project memory) require explicit user
        ratification — the skill never writes them silently."""
        _, body = read_skill("deep-interview")
        low = body.lower()
        guard_tokens = (
            "ratif",
            "ratify",
            "confirm",
            "does not write",
            "does not mutate",
            "no escribe",
            "no muta",
        )
        assert any(tok in low for tok in guard_tokens), (
            "deep-interview body must explicitly guard against silent "
            "mutation of docs or memory (use 'ratif', 'confirm', etc.)."
        )


# ────────────────────────────────────────────────────────────────────────────
# Behavior-specific contracts (E2a — pre-commit-review + simplify)
#
# Lock down the Fase -1 decisions ratified by the user:
#   - `pre-commit-review` delegates to the `code-reviewer` subagent over the
#     branch diff, produces prioritized findings, never rewrites code, never
#     applies fixes, never replaces `simplify`.
#   - `simplify` is a writer scoped strictly to files already in the branch
#     diff: can Edit, cannot create new files, cannot touch files outside the
#     diff. Frames itself as a reducer (not a bug finder) and reports what it
#     simplified and what it chose not to touch.
# ────────────────────────────────────────────────────────────────────────────


class TestPreCommitReviewBehavior:
    def test_delegates_to_code_reviewer(self):
        """The skill must delegate to the `code-reviewer` subagent via the
        Agent tool (same pattern branch-plan established in E1b). The string
        `code-reviewer` is hardcoded with a disclaimer about default-name
        fragility (see .claude/rules/skills.md § Fork / delegación)."""
        _, body = read_skill("pre-commit-review")
        low = body.lower()
        assert "code-reviewer" in low, (
            "pre-commit-review body must name the `code-reviewer` subagent "
            "(the canonical default in Claude Code today) so the delegation "
            "contract is explicit and greppable."
        )
        assert "subagent_type" in low or "agent tool" in low, (
            "pre-commit-review body must reference the Agent-tool delegation "
            "mechanism (e.g., `subagent_type`) so the pattern matches E1b "
            "branch-plan's delegation precedent."
        )

    def test_scope_is_branch_diff(self):
        """Review operates on the branch diff, not the full tree. Body must
        show the exact git invocation (`git diff ... main..HEAD`)."""
        _, body = read_skill("pre-commit-review")
        low = body.lower()
        assert "git diff" in low, (
            "pre-commit-review body must reference `git diff` — scope is the "
            "branch diff, not the working tree nor the full repo."
        )
        assert "main...head" in low, (
            "pre-commit-review body must reference `main...HEAD` to pin the "
            "diff base for the review (merge-base relative, robust to branch state)."
        )

    def test_body_disclaims_writing_and_replacement(self):
        """The skill produces findings, never writes; and it does not
        replace `simplify` (they are complementary, ordered: simplify first,
        then review)."""
        _, body = read_skill("pre-commit-review")
        low = body.lower()
        assert "findings" in low, (
            "pre-commit-review body must mention `findings` as its output "
            "shape — the skill produces prioritized findings, not patches."
        )
        no_write_tokens = (
            "does not rewrite",
            "does not apply",
            "no reescribe",
            "no aplica",
            "not rewrite",
            "not apply",
        )
        assert any(tok in low for tok in no_write_tokens), (
            "pre-commit-review body must explicitly disclaim rewriting code "
            "or applying fixes (use 'does not rewrite', 'no aplica', etc.)."
        )
        assert "simplify" in low, (
            "pre-commit-review body must name `simplify` so its relationship "
            "(complementary, not substitute) is on the page."
        )
        no_replace_tokens = (
            "does not replace",
            "no sustituye",
            "no reemplaza",
            "not a substitute",
        )
        assert any(tok in low for tok in no_replace_tokens), (
            "pre-commit-review body must explicitly disclaim replacing "
            "`simplify` (use 'does not replace', 'no sustituye', etc.)."
        )


class TestSimplifyBehavior:
    def test_allowed_tools_includes_edit(self):
        """`simplify` is a writer scoped to the branch diff. `allowed-tools`
        must include `Edit` — precedent `writing-handoff` (E1a)."""
        fm, _ = read_skill("simplify")
        tools = fm.get("allowed-tools") or []
        assert any(
            isinstance(t, str) and (t == "Edit" or t.startswith("Edit("))
            for t in tools
        ), (
            "simplify frontmatter `allowed-tools` must include `Edit` — the "
            "skill writes changes to files in the branch diff. Got: "
            f"{tools!r}"
        )

    def test_scope_limited_to_branch_diff_no_new_files(self):
        """Writer scope is strict: files already in the diff only, no new
        files, nothing outside the diff. Body must show the exact command
        that derives the scope (`git diff --name-only main..HEAD`) and the
        three explicit disclaims."""
        _, body = read_skill("simplify")
        low = body.lower()
        assert "git diff --name-only" in low and "main...head" in low, (
            "simplify body must reference `git diff --name-only main...HEAD` "
            "so scope derivation is deterministic, greppable, and merge-base robust."
        )
        no_new_files_tokens = (
            "does not create new files",
            "no crea archivos nuevos",
            "no crea nuevos archivos",
            "no new files",
            "never create new files",
        )
        assert any(tok in low for tok in no_new_files_tokens), (
            "simplify body must explicitly disclaim creating new files "
            "(use 'does not create new files', 'no crea archivos nuevos')."
        )
        outside_tokens = (
            "outside the diff",
            "fuera del diff",
            "not in branch diff",
            "no presentes en el diff",
        )
        assert any(tok in low for tok in outside_tokens), (
            "simplify body must explicitly disclaim touching files outside "
            "the branch diff (use 'outside the diff', 'fuera del diff')."
        )

    def test_body_frames_reducer_not_bug_finder(self):
        """simplify reduces redundancy / noise / accidental complexity /
        premature abstraction. It does NOT hunt bugs, does NOT intentionally
        change behavior, does NOT do major refactors."""
        _, body = read_skill("simplify")
        low = body.lower()
        reducer_tokens = (
            "redundan",       # redundancia / redundancy
            "accidental",     # accidental complexity
            "prematura",      # abstracción prematura
            "premature",      # premature abstraction
            "ruido",          # ruido
            "noise",
        )
        assert sum(tok in low for tok in reducer_tokens) >= 2, (
            "simplify body must frame its target (redundancia / ruido / "
            "complejidad accidental / abstracción prematura) — at least two "
            "of those concepts must be named explicitly."
        )
        no_bugs_tokens = (
            "does not find bugs",
            "does not hunt bugs",
            "no busca bugs",
            "not a bug finder",
        )
        assert any(tok in low for tok in no_bugs_tokens), (
            "simplify body must explicitly disclaim bug hunting "
            "(use 'does not find bugs', 'no busca bugs')."
        )
        no_behavior_change_tokens = (
            "does not change behavior",
            "no cambia comportamiento",
            "not change behavior",
            "preserves behavior",
            "preserva comportamiento",
        )
        assert any(tok in low for tok in no_behavior_change_tokens), (
            "simplify body must explicitly disclaim changing behavior "
            "intentionally (use 'does not change behavior', etc.)."
        )
        no_refactor_tokens = (
            "no major refactor",
            "not a major refactor",
            "no refactor mayor",
            "sin refactor mayor",
        )
        assert any(tok in low for tok in no_refactor_tokens), (
            "simplify body must explicitly disclaim doing major refactors "
            "(use 'no major refactor', 'no refactor mayor')."
        )

    def test_body_reports_what_simplified_and_what_skipped(self):
        """At close, the skill must report two lists: what it simplified
        and what it deliberately decided NOT to touch."""
        _, body = read_skill("simplify")
        low = body.lower()
        report_tokens = (
            "reporta",
            "reports",
            "report",
            "summary",
            "resumen",
        )
        assert any(tok in low for tok in report_tokens), (
            "simplify body must describe a reporting step at close "
            "(use 'reporta', 'reports', 'summary')."
        )
        simplified_tokens = (
            "qué simplificó",
            "what was simplified",
            "what it simplified",
            "simplificaciones aplicadas",
            "changes applied",
        )
        assert any(tok in low for tok in simplified_tokens), (
            "simplify body must mention reporting what was simplified "
            "(use 'qué simplificó', 'what was simplified')."
        )
        skipped_tokens = (
            "qué decidió no tocar",
            "what it chose not to touch",
            "decided not to touch",
            "lo que no tocó",
            "intentionally left",
            "deliberadamente dejó",
        )
        assert any(tok in low for tok in skipped_tokens), (
            "simplify body must mention reporting what it chose NOT to "
            "touch (use 'qué decidió no tocar', 'what it chose not to touch')."
        )


# ────────────────────────────────────────────────────────────────────────────
# Behavior-specific contracts (E2b — compress + audit-plugin)
#
# Advisory-only scope in E2b: no enforcement, no writing to files,
# no modification of policy.yaml.
# ────────────────────────────────────────────────────────────────────────────


class TestCompressBehavior:
    def test_body_disclaims_writing_files(self):
        """compress is read-only advisory: it proposes which logs to compress,
        but does NOT write files, delete logs, or modify docs."""
        _, body = read_skill("compress")
        low = body.lower()
        no_write_tokens = (
            "does not write",
            "does not edit",
            "does not delete",
            "does not modify",
            "no escribe",
            "no edita",
            "no elimina",
            "no modifica",
            "read-only",
            "advisory",
        )
        assert any(tok in low for tok in no_write_tokens), (
            "compress body must disclaim writing/editing/deleting files "
            "(use 'does not write', 'read-only', 'advisory', etc.)."
        )

    def test_body_mentions_advisory_and_user_decision(self):
        """User decides whether to archive/summarize logs. Skill proposes."""
        _, body = read_skill("compress")
        low = body.lower()
        assert "advisory" in low or "proposa" in low or "suggest" in low, (
            "compress body must frame itself as advisory (proposes, suggests) "
            "not as a directive (never writes on its own)."
        )

    def test_body_contains_stop_signal(self):
        """compress is read-only advisory: it must signal STOP (skill halts,
        user decides next steps)."""
        _, body = read_skill("compress")
        assert "STOP" in body, (
            "compress body must contain uppercase STOP boundary "
            "(marks advisory-only scope limit)."
        )


class TestAuditPluginBehavior:
    def test_body_mentions_safety_policy(self):
        """audit-plugin audits against SAFETY_POLICY.md checklist."""
        _, body = read_skill("audit-plugin")
        low = body.lower()
        assert "safety_policy" in low or "checklist" in low, (
            "audit-plugin body must reference SAFETY_POLICY.md or "
            "the audit checklist it implements."
        )

    def test_body_disclaims_enforcement_and_installation(self):
        """E2b is advisory-only: no hard enforcement, no tool installation,
        no policy.yaml modification, no audit logs."""
        _, body = read_skill("audit-plugin")
        low = body.lower()
        assert "advisory" in low or "does not install" in low, (
            "audit-plugin body must disclaim enforcement and installation "
            "(frame as advisory, reference E2b limitation)."
        )

    def test_body_contains_stop_signal(self):
        """audit-plugin is advisory-only gate: it must signal STOP (skill returns
        decision, user decides whether to install)."""
        _, body = read_skill("audit-plugin")
        assert "STOP" in body, (
            "audit-plugin body must contain uppercase STOP boundary "
            "(marks advisory-only scope limit)."
        )

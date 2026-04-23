"""Contract tests for the Claude Code Skill primitive used by pos (E1a).

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

# Skill slugs delivered in E1a. Matches policy.yaml.skills_allowed.
E1A_SKILLS = ["project-kickoff", "writing-handoff"]

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
    @pytest.mark.parametrize("slug", E1A_SKILLS)
    def test_skill_dir_exists(self, slug: str):
        assert (SKILLS_DIR / slug).is_dir()

    @pytest.mark.parametrize("slug", E1A_SKILLS)
    def test_skill_md_exists(self, slug: str):
        assert (SKILLS_DIR / slug / "SKILL.md").is_file()

    @pytest.mark.parametrize("slug", E1A_SKILLS)
    def test_skill_md_parses(self, slug: str):
        fm, body = read_skill(slug)
        assert fm and body

    @pytest.mark.parametrize("slug", E1A_SKILLS)
    def test_no_skill_json(self, slug: str):
        """skill.json is not part of the official primitive. Don't emit it."""
        assert not (SKILLS_DIR / slug / "skill.json").exists()


# ────────────────────────────────────────────────────────────────────────────
# Frontmatter: minimal, no invented fields
# ────────────────────────────────────────────────────────────────────────────


class TestFrontmatter:
    @pytest.mark.parametrize("slug", E1A_SKILLS)
    def test_required_keys_present(self, slug: str):
        fm, _ = read_skill(slug)
        missing = REQUIRED_FRONTMATTER_KEYS - set(fm)
        assert not missing, (
            f"Skill '{slug}' frontmatter missing required keys: {missing}"
        )

    @pytest.mark.parametrize("slug", E1A_SKILLS)
    def test_no_invented_fields(self, slug: str):
        """Only the official three fields are allowed. Adding more requires a
        citation (see feedback memory 'Skill primitive stays minimal')."""
        fm, _ = read_skill(slug)
        extra = set(fm) - ALLOWED_FRONTMATTER_KEYS
        assert not extra, (
            f"Skill '{slug}' frontmatter has non-official fields: {extra}. "
            "Remove them or justify with an official Claude Code doc citation."
        )

    @pytest.mark.parametrize("slug", E1A_SKILLS)
    def test_name_matches_dir(self, slug: str):
        fm, _ = read_skill(slug)
        assert fm["name"] == slug, (
            f"frontmatter name={fm['name']!r} does not match dir name={slug!r}"
        )

    @pytest.mark.parametrize("slug", E1A_SKILLS)
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

    @pytest.mark.parametrize("slug", E1A_SKILLS)
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

    @pytest.mark.parametrize("slug", E1A_SKILLS)
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
    @pytest.mark.parametrize("slug", E1A_SKILLS)
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

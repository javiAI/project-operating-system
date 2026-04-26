"""Contract tests for the Claude Code Plugin Agent primitive used by pos (F2).

Scope:
  - Frontmatter shape (official primitive: name + description + tools + model).
  - No invented fields beyond {name, description, tools, model}.
  - `name` matches the filename without `.md`.
  - description non-empty.
  - tools is REQUIRED and is a comma-separated string (per official subagent docs).
  - model is REQUIRED and one of the supported values; F2 agents declare `sonnet`.
  - Body (system prompt) is substantive.

F2 Fase -1 ratified decisions:
  - 2 agents only: pos-code-reviewer + pos-architect (auditor deferred — no
    consumer hoy, regla #7 CLAUDE.md).
  - Namespace `pos-*` to avoid collision with built-in / user / project agents.
  - No `agents_allowed` in policy.yaml in F2 (no enforcement consumer yet).

Capability surfaces locked here are mirrored by the skills that delegate to
each agent:
  - pre-commit-review (E2a) → pos-code-reviewer (bugs / security / scope / invariants).
  - compound (E3a) → pos-architect (patterns / design / cross-file consistency).
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = REPO_ROOT / "agents"

ALLOWED_AGENTS = ["pos-code-reviewer", "pos-architect"]

ALLOWED_FRONTMATTER_KEYS = {"name", "description", "tools", "model"}
REQUIRED_FRONTMATTER_KEYS = {"name", "description", "tools", "model"}
VALID_MODELS = {"sonnet", "opus", "haiku"}
F2_REQUIRED_MODEL = "sonnet"


def read_agent(slug: str) -> tuple[dict, str]:
    """Return `(frontmatter, body)` for `agents/<slug>.md`.

    Raises `AssertionError` with a clear reason if the shape is wrong — this
    is a contract test, explicit failure beats KeyError.
    """
    path = AGENTS_DIR / f"{slug}.md"
    assert path.exists(), f"Agent file missing: {path}"
    raw = path.read_text(encoding="utf-8")
    parts = raw.split("---\n", 2)
    assert len(parts) >= 3 and parts[0] == "", (
        f"Agent {slug}.md does not start with `---\\n<yaml>\\n---\\n` "
        f"frontmatter (got: {parts[0]!r}...)"
    )
    frontmatter = yaml.safe_load(parts[1]) or {}
    body = parts[2]
    assert isinstance(frontmatter, dict), (
        f"Agent {slug} frontmatter must parse as a YAML mapping, "
        f"got {type(frontmatter).__name__}"
    )
    return frontmatter, body


# ────────────────────────────────────────────────────────────────────────────
# Structure: file exists and parses as frontmatter + body
# ────────────────────────────────────────────────────────────────────────────


class TestStructure:
    @pytest.mark.parametrize("slug", ALLOWED_AGENTS)
    def test_agent_file_exists(self, slug: str):
        assert (AGENTS_DIR / f"{slug}.md").is_file(), (
            f"Agent file `agents/{slug}.md` missing — F2 declares 2 agents "
            f"in ALLOWED_AGENTS."
        )

    @pytest.mark.parametrize("slug", ALLOWED_AGENTS)
    def test_agent_md_parses(self, slug: str):
        fm, body = read_agent(slug)
        assert fm
        assert body.strip()


# ────────────────────────────────────────────────────────────────────────────
# Frontmatter contract: name / description / tools / model only
# ────────────────────────────────────────────────────────────────────────────


class TestFrontmatter:
    @pytest.mark.parametrize("slug", ALLOWED_AGENTS)
    def test_frontmatter_keys_subset(self, slug: str):
        fm, _ = read_agent(slug)
        extra = set(fm.keys()) - ALLOWED_FRONTMATTER_KEYS
        assert not extra, (
            f"Agent {slug} frontmatter has unexpected keys: {sorted(extra)}. "
            f"Allowed (per official Claude Code subagent docs): "
            f"{sorted(ALLOWED_FRONTMATTER_KEYS)}. F2 Fase -1 ratified: no "
            f"invented fields."
        )

    @pytest.mark.parametrize("slug", ALLOWED_AGENTS)
    def test_required_keys_present(self, slug: str):
        fm, _ = read_agent(slug)
        missing = REQUIRED_FRONTMATTER_KEYS - set(fm.keys())
        assert not missing, (
            f"Agent {slug} missing required frontmatter keys: {sorted(missing)}"
        )

    @pytest.mark.parametrize("slug", ALLOWED_AGENTS)
    def test_name_matches_filename(self, slug: str):
        fm, _ = read_agent(slug)
        assert fm.get("name") == slug, (
            f"Agent {slug} frontmatter name={fm.get('name')!r} must match "
            f"filename `{slug}.md` (convention)."
        )

    @pytest.mark.parametrize("slug", ALLOWED_AGENTS)
    def test_name_uses_pos_namespace(self, slug: str):
        fm, _ = read_agent(slug)
        name = fm.get("name", "")
        assert isinstance(name, str) and name.startswith("pos-"), (
            f"Agent {slug} name={name!r} must use `pos-*` namespace to avoid "
            f"collision with built-in / user / project agents (F2 decision)."
        )

    @pytest.mark.parametrize("slug", ALLOWED_AGENTS)
    def test_description_non_empty_string(self, slug: str):
        fm, _ = read_agent(slug)
        desc = fm.get("description", "")
        assert isinstance(desc, str) and desc.strip(), (
            f"Agent {slug} description must be non-empty string"
        )

    @pytest.mark.parametrize("slug", ALLOWED_AGENTS)
    def test_tools_is_comma_separated_string(self, slug: str):
        fm, _ = read_agent(slug)
        tools = fm["tools"]
        assert isinstance(tools, str), (
            f"Agent {slug} tools must be a comma-separated string per "
            f"official Claude Code subagent docs, got "
            f"{type(tools).__name__}. (Skill primitive uses YAML list, but "
            f"agent primitive uses comma-separated string — different shapes.)"
        )
        assert tools.strip(), f"Agent {slug} tools must be non-empty"
        tokens = [t.strip() for t in tools.split(",")]
        assert all(tokens), (
            f"Agent {slug} tools={tools!r} has empty token after split — "
            f"comma-separated format requires non-empty tokens between commas."
        )
        assert all(" " not in t.split("(", 1)[0] for t in tokens), (
            f"Agent {slug} tools={tools!r} contains a token with whitespace "
            f"in its tool name (before any `(...)` scope). Format must be "
            f"`Tool1, Tool2, Bash(cmd:*)` — comma-separated, not space-separated."
        )

    @pytest.mark.parametrize("slug", ALLOWED_AGENTS)
    def test_model_valid(self, slug: str):
        fm, _ = read_agent(slug)
        model = fm["model"]
        assert model in VALID_MODELS, (
            f"Agent {slug} model={model!r} must be one of "
            f"{sorted(VALID_MODELS)}"
        )

    @pytest.mark.parametrize("slug", ALLOWED_AGENTS)
    def test_model_is_sonnet_for_f2(self, slug: str):
        """F2 Fase -1 decision (1) ratified `model: sonnet` for both agents.
        Lock that decision here so a future drift to opus/haiku is explicit."""
        fm, _ = read_agent(slug)
        assert fm["model"] == F2_REQUIRED_MODEL, (
            f"Agent {slug} model={fm['model']!r} must be "
            f"{F2_REQUIRED_MODEL!r} per F2 Fase -1 decision (1). Bumping to "
            f"opus/haiku requires a new branch + ratification."
        )


# ────────────────────────────────────────────────────────────────────────────
# Body: system prompt is substantive
# ────────────────────────────────────────────────────────────────────────────


class TestBody:
    @pytest.mark.parametrize("slug", ALLOWED_AGENTS)
    def test_body_substantive(self, slug: str):
        _, body = read_agent(slug)
        assert len(body.strip()) > 100, (
            f"Agent {slug} body must be substantive (>100 chars); body acts "
            f"as the system prompt for the subagent."
        )


# ────────────────────────────────────────────────────────────────────────────
# Capability contracts: lock down what each agent declares it can do
# ────────────────────────────────────────────────────────────────────────────


class TestCodeReviewerCapability:
    """pos-code-reviewer is consumed by pre-commit-review (E2a). Body must
    document the capability surface the skill delegates to."""

    def test_body_mentions_review_capabilities(self):
        _, body = read_agent("pos-code-reviewer")
        low = body.lower()
        for keyword in ("bug", "security", "scope", "invariant"):
            assert keyword in low, (
                f"pos-code-reviewer body must mention `{keyword}` as part "
                f"of its review capability surface (consumed by "
                f"pre-commit-review)."
            )


class TestArchitectCapability:
    """pos-architect is consumed by compound (E3a). Body must document the
    architecture/pattern analysis surface the skill delegates to."""

    def test_body_mentions_pattern_capability(self):
        _, body = read_agent("pos-architect")
        assert "pattern" in body.lower(), (
            "pos-architect body must mention `pattern` (consumed by compound "
            "for code pattern extraction)."
        )

    def test_body_mentions_design_or_architecture(self):
        _, body = read_agent("pos-architect")
        low = body.lower()
        assert "design" in low or "architectur" in low, (
            "pos-architect body must mention `design` or `architectur` "
            "(architectural lens)."
        )

    def test_body_mentions_cross_file_consistency(self):
        _, body = read_agent("pos-architect")
        low = body.lower()
        assert "cross-file" in low or "cross file" in low or "consistency" in low, (
            "pos-architect body must reference cross-file consistency "
            "analysis (reviewing design decisions across files)."
        )

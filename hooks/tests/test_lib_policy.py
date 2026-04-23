"""Tests for hooks/_lib/policy.py — declarative policy loader."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "policy"


@pytest.fixture(autouse=True)
def clear_cache():
    from _lib import policy as pol
    pol.reset_cache()
    yield
    pol.reset_cache()


@pytest.fixture
def repo_with_policy(tmp_path: Path):
    def _factory(fixture_name: str) -> Path:
        src = FIXTURES_DIR / fixture_name
        dst = tmp_path / "policy.yaml"
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        return tmp_path
    return _factory


# -------------------- load_policy ----------------------------------------


class TestLoadPolicy:
    def test_missing_file_returns_none(self, tmp_path):
        from _lib import policy
        assert policy.load_policy(tmp_path) is None

    def test_valid_yaml_returns_dict(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        data = policy.load_policy(root)
        assert isinstance(data, dict)
        assert data["version"] == "0.1.0"
        assert data["project"] == "test-fixture"

    def test_minimal_yaml_returns_dict(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("minimal.yaml")
        data = policy.load_policy(root)
        assert isinstance(data, dict)
        assert data["project"] == "test-minimal"

    def test_malformed_yaml_returns_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("malformed.yaml")
        assert policy.load_policy(root) is None

    def test_top_level_non_dict_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text("- a\n- b\n- c\n", encoding="utf-8")
        assert policy.load_policy(tmp_path) is None

    def test_empty_yaml_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text("", encoding="utf-8")
        assert policy.load_policy(tmp_path) is None

    def test_top_level_scalar_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text("just-a-string\n", encoding="utf-8")
        assert policy.load_policy(tmp_path) is None

    def test_cache_returns_same_object(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        a = policy.load_policy(root)
        b = policy.load_policy(root)
        assert a is b

    def test_reset_cache_clears(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        a = policy.load_policy(root)
        policy.reset_cache()
        b = policy.load_policy(root)
        assert a is not b
        assert a == b

    def test_cache_keyed_by_path(self, tmp_path, repo_with_policy):
        from _lib import policy
        root_a = repo_with_policy("full.yaml")
        a = policy.load_policy(root_a)
        root_b = tmp_path / "other"
        root_b.mkdir()
        (root_b / "policy.yaml").write_text("version: \"9.9.9\"\n", encoding="utf-8")
        b = policy.load_policy(root_b)
        assert a is not b
        assert b["version"] == "9.9.9"


# -------------------- docs_sync_rules ------------------------------------


class TestDocsSyncRules:
    def test_full_policy_baseline(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        rules = policy.docs_sync_rules(root)
        assert rules is not None
        assert rules.baseline == ("ROADMAP.md", "HANDOFF.md")

    def test_full_policy_conditional_count(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        rules = policy.docs_sync_rules(root)
        assert len(rules.conditional) == 4

    def test_conditional_excludes_captured(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        rules = policy.docs_sync_rules(root)
        hooks_rule = next(r for r in rules.conditional if "hooks/**" in r.if_touched)
        assert hooks_rule.excludes == ("hooks/tests/**",)

    def test_conditional_no_excludes_defaults_empty(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        rules = policy.docs_sync_rules(root)
        gen_rule = next(r for r in rules.conditional if "generator/**" in r.if_touched)
        assert gen_rule.excludes == ()

    def test_missing_section_returns_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("minimal.yaml")
        assert policy.docs_sync_rules(root) is None

    def test_partial_policy_empty_conditional(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("missing-section.yaml")
        rules = policy.docs_sync_rules(root)
        assert rules is not None
        assert rules.baseline == ("ROADMAP.md", "HANDOFF.md")
        assert rules.conditional == ()

    def test_missing_file_returns_none(self, tmp_path):
        from _lib import policy
        assert policy.docs_sync_rules(tmp_path) is None

    def test_malformed_yaml_returns_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("malformed.yaml")
        assert policy.docs_sync_rules(root) is None

    def test_missing_baseline_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  pre_pr:\n    docs_sync_conditional: []\n",
            encoding="utf-8",
        )
        assert policy.docs_sync_rules(tmp_path) is None

    def test_conditional_rule_missing_then_required_skipped(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  pre_pr:\n"
            "    docs_sync_required: [\"ROADMAP.md\"]\n"
            "    docs_sync_conditional:\n"
            "      - if_touched: [\"generator/**\"]\n"
            "        then_required: [\"docs/ARCHITECTURE.md\"]\n"
            "      - if_touched: [\"bad/**\"]\n"
            "      - if_touched: [\"skills/**\"]\n"
            "        then_required: [\".claude/rules/skills-map.md\"]\n",
            encoding="utf-8",
        )
        rules = policy.docs_sync_rules(tmp_path)
        assert rules is not None
        assert len(rules.conditional) == 2

    def test_conditional_non_dict_entry_skipped(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  pre_pr:\n"
            "    docs_sync_required: [\"ROADMAP.md\"]\n"
            "    docs_sync_conditional:\n"
            "      - \"not-a-mapping\"\n"
            "      - if_touched: [\"generator/**\"]\n"
            "        then_required: [\"docs/ARCHITECTURE.md\"]\n",
            encoding="utf-8",
        )
        rules = policy.docs_sync_rules(tmp_path)
        assert rules is not None
        assert len(rules.conditional) == 1


# -------------------- post_merge_trigger ---------------------------------


class TestPostMergeTrigger:
    def test_full_policy(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        t = policy.post_merge_trigger(root)
        assert t is not None
        assert "hooks/**" in t.touched_paths_any_of
        assert "docs/**" in t.skip_if_only
        assert t.min_files_changed == 2

    def test_missing_section_returns_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("minimal.yaml")
        assert policy.post_merge_trigger(root) is None

    def test_missing_file_returns_none(self, tmp_path):
        from _lib import policy
        assert policy.post_merge_trigger(tmp_path) is None

    def test_malformed_yaml_returns_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("malformed.yaml")
        assert policy.post_merge_trigger(root) is None

    def test_missing_min_files_changed_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  post_merge:\n"
            "    skills_conditional:\n"
            "      - skill: \"pos:compound\"\n"
            "        trigger:\n"
            "          touched_paths_any_of: [\"hooks/**\"]\n"
            "          skip_if_only: []\n",
            encoding="utf-8",
        )
        assert policy.post_merge_trigger(tmp_path) is None

    def test_min_files_non_int_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  post_merge:\n"
            "    skills_conditional:\n"
            "      - trigger:\n"
            "          touched_paths_any_of: [\"hooks/**\"]\n"
            "          min_files_changed: \"two\"\n",
            encoding="utf-8",
        )
        assert policy.post_merge_trigger(tmp_path) is None

    def test_missing_touched_paths_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  post_merge:\n"
            "    skills_conditional:\n"
            "      - trigger:\n"
            "          min_files_changed: 2\n",
            encoding="utf-8",
        )
        assert policy.post_merge_trigger(tmp_path) is None

    def test_missing_skip_if_only_defaults_empty(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  post_merge:\n"
            "    skills_conditional:\n"
            "      - trigger:\n"
            "          touched_paths_any_of: [\"hooks/**\"]\n"
            "          min_files_changed: 2\n",
            encoding="utf-8",
        )
        t = policy.post_merge_trigger(tmp_path)
        assert t is not None
        assert t.skip_if_only == ()

    def test_empty_skills_conditional_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  post_merge:\n    skills_conditional: []\n",
            encoding="utf-8",
        )
        assert policy.post_merge_trigger(tmp_path) is None

    def test_skills_conditional_non_list_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  post_merge:\n    skills_conditional: \"bad\"\n",
            encoding="utf-8",
        )
        assert policy.post_merge_trigger(tmp_path) is None


# -------------------- pre_write_rules ------------------------------------


class TestPreWriteRules:
    def test_full_policy(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        rules = policy.pre_write_rules(root)
        assert rules is not None
        labels = [p.label for p in rules.enforced_patterns]
        assert labels == ["hooks_top_level_py", "generator_ts"]

    def test_hooks_pattern(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        rules = policy.pre_write_rules(root)
        hooks = next(p for p in rules.enforced_patterns if p.label == "hooks_top_level_py")
        assert hooks.match_glob == "hooks/*.py"
        assert "hooks/tests/**" in hooks.exclude_globs
        assert "hooks/_lib/**" in hooks.exclude_globs

    def test_generator_pattern(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        rules = policy.pre_write_rules(root)
        gen = next(p for p in rules.enforced_patterns if p.label == "generator_ts")
        assert gen.match_glob == "generator/**/*.ts"
        assert "**/*.test.ts" in gen.exclude_globs
        assert "generator/__tests__/**" in gen.exclude_globs
        assert "generator/__fixtures__/**" in gen.exclude_globs

    def test_missing_section_returns_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("minimal.yaml")
        assert policy.pre_write_rules(root) is None

    def test_missing_file_returns_none(self, tmp_path):
        from _lib import policy
        assert policy.pre_write_rules(tmp_path) is None

    def test_malformed_yaml_returns_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("malformed.yaml")
        assert policy.pre_write_rules(root) is None

    def test_invalid_entries_skipped(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  pre_write:\n"
            "    enforced_patterns:\n"
            "      - label: \"ok\"\n"
            "        match_glob: \"a/*.py\"\n"
            "      - \"not-a-mapping\"\n"
            "      - label: \"no_match_glob\"\n"
            "      - match_glob: \"b/*.ts\"\n",
            encoding="utf-8",
        )
        rules = policy.pre_write_rules(tmp_path)
        assert rules is not None
        assert len(rules.enforced_patterns) == 1
        assert rules.enforced_patterns[0].label == "ok"

    def test_enforced_patterns_non_list_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  pre_write:\n    enforced_patterns: \"bad\"\n",
            encoding="utf-8",
        )
        assert policy.pre_write_rules(tmp_path) is None

    def test_exclude_globs_default_empty(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  pre_write:\n"
            "    enforced_patterns:\n"
            "      - label: \"bare\"\n"
            "        match_glob: \"a/*.py\"\n",
            encoding="utf-8",
        )
        rules = policy.pre_write_rules(tmp_path)
        assert rules is not None
        assert rules.enforced_patterns[0].exclude_globs == ()


# -------------------- derive_test_pair -----------------------------------


class TestDeriveTestPair:
    def test_hooks_top_level_py(self):
        from _lib import policy
        assert policy.derive_test_pair("hooks/foo.py", "hooks_top_level_py") == \
            "hooks/tests/test_foo.py"

    def test_hooks_top_level_py_with_hyphens(self):
        from _lib import policy
        assert policy.derive_test_pair("hooks/foo-bar.py", "hooks_top_level_py") == \
            "hooks/tests/test_foo_bar.py"

    def test_hooks_top_level_py_multiple_hyphens(self):
        from _lib import policy
        assert policy.derive_test_pair("hooks/pre-pr-gate.py", "hooks_top_level_py") == \
            "hooks/tests/test_pre_pr_gate.py"

    def test_generator_ts_top(self):
        from _lib import policy
        assert policy.derive_test_pair("generator/run.ts", "generator_ts") == \
            "generator/run.test.ts"

    def test_generator_ts_nested(self):
        from _lib import policy
        assert policy.derive_test_pair("generator/lib/foo/bar.ts", "generator_ts") == \
            "generator/lib/foo/bar.test.ts"

    def test_unknown_label_returns_none(self):
        from _lib import policy
        assert policy.derive_test_pair("hooks/foo.py", "unknown_label") is None

    def test_label_hooks_but_non_py_returns_none(self):
        from _lib import policy
        assert policy.derive_test_pair("hooks/foo.ts", "hooks_top_level_py") is None

    def test_label_generator_but_non_ts_returns_none(self):
        from _lib import policy
        assert policy.derive_test_pair("generator/foo.py", "generator_ts") is None

    def test_label_hooks_path_not_in_hooks_returns_none(self):
        from _lib import policy
        assert policy.derive_test_pair("other/foo.py", "hooks_top_level_py") is None


# -------------------- pre_compact_rules (D6) -----------------------------


class TestPreCompactRules:
    def test_full_policy(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        rules = policy.pre_compact_rules(root)
        assert rules is not None
        assert rules.persist == (
            "decisions_in_flight",
            "phase_minus_one_state",
            "unsaved_pattern_candidates",
        )

    def test_missing_section_returns_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("minimal.yaml")
        assert policy.pre_compact_rules(root) is None

    def test_missing_file_returns_none(self, tmp_path):
        from _lib import policy
        assert policy.pre_compact_rules(tmp_path) is None

    def test_malformed_yaml_returns_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("malformed.yaml")
        assert policy.pre_compact_rules(root) is None

    def test_persist_missing_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  pre_compact: {}\n", encoding="utf-8"
        )
        assert policy.pre_compact_rules(tmp_path) is None

    def test_persist_non_list_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  pre_compact:\n    persist: \"bad\"\n",
            encoding="utf-8",
        )
        assert policy.pre_compact_rules(tmp_path) is None

    def test_persist_mixed_types_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  pre_compact:\n    persist: [a, 42]\n",
            encoding="utf-8",
        )
        assert policy.pre_compact_rules(tmp_path) is None

    def test_persist_empty_list_returns_empty_tuple(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  pre_compact:\n    persist: []\n",
            encoding="utf-8",
        )
        rules = policy.pre_compact_rules(tmp_path)
        assert rules is not None
        assert rules.persist == ()

    def test_pre_compact_non_mapping_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  pre_compact: 42\n", encoding="utf-8"
        )
        assert policy.pre_compact_rules(tmp_path) is None


# -------------------- skills_allowed_list (D6) ---------------------------


class TestSkillsAllowedList:
    def test_full_policy(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("full.yaml")
        allowed = policy.skills_allowed_list(root)
        assert allowed == ("pos:kickoff", "pos:branch-plan", "pos:handoff-write")

    def test_missing_section_returns_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("minimal.yaml")
        assert policy.skills_allowed_list(root) is None

    def test_missing_file_returns_none(self, tmp_path):
        from _lib import policy
        assert policy.skills_allowed_list(tmp_path) is None

    def test_malformed_yaml_returns_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("malformed.yaml")
        assert policy.skills_allowed_list(root) is None

    def test_empty_list_returns_empty_tuple(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "skills_allowed: []\n", encoding="utf-8"
        )
        allowed = policy.skills_allowed_list(tmp_path)
        assert allowed == ()

    def test_wrong_shape_returns_invalid_sentinel(self, tmp_path):
        """Scalar instead of list → SKILLS_ALLOWED_INVALID (NOT None)."""
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "skills_allowed: \"not-a-list\"\n", encoding="utf-8"
        )
        assert policy.skills_allowed_list(tmp_path) is policy.SKILLS_ALLOWED_INVALID

    def test_mixed_types_returns_invalid_sentinel(self, tmp_path):
        """List with non-string element → SKILLS_ALLOWED_INVALID."""
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "skills_allowed: [\"pos:kickoff\", 42]\n", encoding="utf-8"
        )
        assert policy.skills_allowed_list(tmp_path) is policy.SKILLS_ALLOWED_INVALID

    def test_dict_shape_returns_invalid_sentinel(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "skills_allowed:\n  a: 1\n", encoding="utf-8"
        )
        assert policy.skills_allowed_list(tmp_path) is policy.SKILLS_ALLOWED_INVALID

    def test_invalid_sentinel_distinct_from_none(self, tmp_path):
        """Absent and invalid must NOT collapse to the same value.

        Consumers rely on this distinction: absent → deferred (valid state),
        invalid → misconfigured (observable policy error).
        """
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "version: \"0.1.0\"\n", encoding="utf-8"
        )
        absent = policy.skills_allowed_list(tmp_path)
        assert absent is None
        policy.reset_cache()
        (tmp_path / "policy.yaml").write_text(
            "skills_allowed: \"bad\"\n", encoding="utf-8"
        )
        invalid = policy.skills_allowed_list(tmp_path)
        assert invalid is policy.SKILLS_ALLOWED_INVALID
        assert invalid is not None  # belt-and-suspenders

    def test_explicit_empty_distinct_from_missing(self, tmp_path):
        """`skills_allowed: []` → `()` (deny-all); absent → None (deferred)."""
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "skills_allowed: []\n", encoding="utf-8"
        )
        assert policy.skills_allowed_list(tmp_path) == ()
        policy.reset_cache()
        (tmp_path / "policy.yaml").write_text("version: \"1.0.0\"\n", encoding="utf-8")
        assert policy.skills_allowed_list(tmp_path) is None

    def test_three_states_are_all_distinct(self, tmp_path):
        """None (absent) vs SKILLS_ALLOWED_INVALID vs tuple — three states.

        Before this fix, `None` collapsed absent + invalid, which let a typo
        silently turn enforcement off. The accessor must keep them distinct.
        """
        from _lib import policy
        # absent → None
        (tmp_path / "policy.yaml").write_text("version: \"0.1.0\"\n", encoding="utf-8")
        assert policy.skills_allowed_list(tmp_path) is None
        # invalid → sentinel
        policy.reset_cache()
        (tmp_path / "policy.yaml").write_text(
            "skills_allowed: 42\n", encoding="utf-8"
        )
        assert policy.skills_allowed_list(tmp_path) is policy.SKILLS_ALLOWED_INVALID
        # valid → tuple
        policy.reset_cache()
        (tmp_path / "policy.yaml").write_text(
            "skills_allowed: [\"pos:kickoff\"]\n", encoding="utf-8"
        )
        assert policy.skills_allowed_list(tmp_path) == ("pos:kickoff",)


# -------------------- failure mode (c.2) ---------------------------------


class TestFailureMode:
    """Corrupt/missing policy → None, no exception. Enables hook pass-through."""

    def test_malformed_all_queries_return_none(self, repo_with_policy):
        from _lib import policy
        root = repo_with_policy("malformed.yaml")
        assert policy.load_policy(root) is None
        assert policy.docs_sync_rules(root) is None
        assert policy.post_merge_trigger(root) is None
        assert policy.pre_write_rules(root) is None
        assert policy.pre_compact_rules(root) is None
        assert policy.skills_allowed_list(root) is None

    def test_missing_file_all_queries_return_none(self, tmp_path):
        from _lib import policy
        assert policy.load_policy(tmp_path) is None
        assert policy.docs_sync_rules(tmp_path) is None
        assert policy.post_merge_trigger(tmp_path) is None
        assert policy.pre_write_rules(tmp_path) is None
        assert policy.pre_compact_rules(tmp_path) is None
        assert policy.skills_allowed_list(tmp_path) is None

    def test_empty_file_all_queries_return_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text("", encoding="utf-8")
        assert policy.load_policy(tmp_path) is None
        assert policy.docs_sync_rules(tmp_path) is None

    def test_yaml_parse_exception_not_propagated(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text("key: [broken\n", encoding="utf-8")
        try:
            policy.load_policy(tmp_path)
        except Exception as e:  # pragma: no cover
            pytest.fail(f"load_policy raised: {e!r}")


# -------------------- wrong-shape guards (round 2) -----------------------


class TestWrongShapeGuards:
    """Accessors must return None (never AttributeError) on wrong-shape YAML."""

    def test_lifecycle_string_docs_sync(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text("lifecycle: not_a_mapping\n", encoding="utf-8")
        assert policy.docs_sync_rules(tmp_path) is None

    def test_lifecycle_string_post_merge(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text("lifecycle: not_a_mapping\n", encoding="utf-8")
        assert policy.post_merge_trigger(tmp_path) is None

    def test_lifecycle_string_pre_write(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text("lifecycle: not_a_mapping\n", encoding="utf-8")
        assert policy.pre_write_rules(tmp_path) is None

    def test_lifecycle_list_docs_sync(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text("lifecycle: [a, b]\n", encoding="utf-8")
        assert policy.docs_sync_rules(tmp_path) is None

    def test_pre_pr_non_mapping(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  pre_pr: just_a_string\n", encoding="utf-8"
        )
        assert policy.docs_sync_rules(tmp_path) is None

    def test_post_merge_non_mapping(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  post_merge: 42\n", encoding="utf-8"
        )
        assert policy.post_merge_trigger(tmp_path) is None

    def test_pre_write_non_mapping(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  pre_write: [wrong]\n", encoding="utf-8"
        )
        assert policy.pre_write_rules(tmp_path) is None

    def test_lifecycle_string_pre_compact(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text("lifecycle: not_a_mapping\n", encoding="utf-8")
        assert policy.pre_compact_rules(tmp_path) is None

    def test_pre_compact_non_mapping(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n  pre_compact: [wrong]\n", encoding="utf-8"
        )
        assert policy.pre_compact_rules(tmp_path) is None


class TestOptionalListShape:
    """`excludes`/`skip_if_only`/`exclude_globs` distinguish missing vs wrong-type."""

    def test_conditional_excludes_wrong_type_skips_rule(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  pre_pr:\n"
            "    docs_sync_required: [ROADMAP.md]\n"
            "    docs_sync_conditional:\n"
            "      - if_touched: [generator/]\n"
            "        then_required: [docs/ARCHITECTURE.md]\n"
            "        excludes: not_a_list\n"
            "      - if_touched: [hooks/]\n"
            "        then_required: [docs/ARCHITECTURE.md]\n",
            encoding="utf-8",
        )
        rules = policy.docs_sync_rules(tmp_path)
        assert rules is not None
        assert len(rules.conditional) == 1
        assert rules.conditional[0].if_touched == ("hooks/",)

    def test_skip_if_only_wrong_type_returns_none(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  post_merge:\n"
            "    skills_conditional:\n"
            "      - skill: /pos:compound\n"
            "        trigger:\n"
            "          touched_paths_any_of: [hooks/**]\n"
            "          skip_if_only: 'docs/**'\n"
            "          min_files_changed: 1\n",
            encoding="utf-8",
        )
        assert policy.post_merge_trigger(tmp_path) is None

    def test_exclude_globs_wrong_type_skips_pattern(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  pre_write:\n"
            "    enforced_patterns:\n"
            "      - label: a\n"
            "        match_glob: hooks/*.py\n"
            "        exclude_globs: not_a_list\n"
            "      - label: b\n"
            "        match_glob: generator/*.ts\n",
            encoding="utf-8",
        )
        rules = policy.pre_write_rules(tmp_path)
        assert rules is not None
        assert [p.label for p in rules.enforced_patterns] == ["b"]

    def test_safe_str_list_mixed_types_returns_none_propagates_to_accessor(self, tmp_path):
        from _lib import policy
        (tmp_path / "policy.yaml").write_text(
            "lifecycle:\n"
            "  pre_pr:\n"
            "    docs_sync_required: [ROADMAP.md, 42]\n"
            "    docs_sync_conditional: []\n",
            encoding="utf-8",
        )
        assert policy.docs_sync_rules(tmp_path) is None


# -------------------- real repo policy -----------------------------------


class TestRealRepoPolicy:
    """Smoke check: the repo's own policy.yaml loads cleanly."""

    def test_real_policy_loads(self):
        from _lib import policy
        repo_root = Path(__file__).resolve().parents[2]
        assert (repo_root / "policy.yaml").exists()
        data = policy.load_policy(repo_root)
        assert isinstance(data, dict)

    def test_real_docs_sync_rules(self):
        from _lib import policy
        repo_root = Path(__file__).resolve().parents[2]
        rules = policy.docs_sync_rules(repo_root)
        assert rules is not None
        assert "ROADMAP.md" in rules.baseline
        assert "HANDOFF.md" in rules.baseline

    def test_real_post_merge_trigger(self):
        from _lib import policy
        repo_root = Path(__file__).resolve().parents[2]
        t = policy.post_merge_trigger(repo_root)
        assert t is not None
        assert t.min_files_changed >= 1

    def test_real_pre_write_rules(self):
        from _lib import policy
        repo_root = Path(__file__).resolve().parents[2]
        rules = policy.pre_write_rules(repo_root)
        assert rules is not None
        labels = [p.label for p in rules.enforced_patterns]
        assert "hooks_top_level_py" in labels
        assert "generator_ts" in labels

    def test_real_pre_compact_rules(self):
        """Meta-repo policy declares pre_compact.persist → loader returns rules."""
        from _lib import policy
        repo_root = Path(__file__).resolve().parents[2]
        rules = policy.pre_compact_rules(repo_root)
        assert rules is not None
        assert "decisions_in_flight" in rules.persist
        assert "phase_minus_one_state" in rules.persist
        assert "unsaved_pattern_candidates" in rules.persist

    def test_real_skills_allowed_populated_by_e1b(self):
        """E1a populated `skills_allowed` with the first two real skills;
        E1b extends it with the Fase -1 pair (branch-plan + deep-interview).
        Accessor returns the full 4-tuple — locks down the contract between
        `policy.yaml.skills_allowed` and the loader against silent drift.
        """
        from _lib import policy
        repo_root = Path(__file__).resolve().parents[2]
        assert policy.skills_allowed_list(repo_root) == (
            "project-kickoff",
            "writing-handoff",
            "branch-plan",
            "deep-interview",
        )

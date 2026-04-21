"""Tests for hooks/pre-write-guard.py.

D3 blocker hook — enforces test-pair existence on Writes to enforced paths
(generator/**/*.ts and hooks/*.py top-level). See CLAUDE.md regla #3.

Crystal-clear contract this suite locks in:
- enforced path + file does NOT exist yet + no test pair  → deny (exit 2)
- enforced path + file does NOT exist yet + test pair exists → allow (exit 0)
- enforced path + file ALREADY exists (any state)         → allow (exit 0)
- excluded path (tests/docs/templates/meta OR _lib helper)  → pass-through silent
- non-Write tool                                          → pass-through silent
"""
from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "hooks" / "pre-write-guard.py"
FIXTURES = Path(__file__).parent / "fixtures" / "payloads"

_spec = importlib.util.spec_from_file_location("pre_write_guard", HOOK)
assert _spec is not None and _spec.loader is not None
pwg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pwg)


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def run_hook(payload: dict | str, cwd: Path) -> subprocess.CompletedProcess:
    stdin = json.dumps(payload) if isinstance(payload, dict) else payload
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=5,
    )


def parse_stdout(result: subprocess.CompletedProcess) -> dict:
    return json.loads(result.stdout)


def make_write(file_path: str, content: str = "x") -> dict:
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": content},
    }


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Synthetic repo root with the dirs the hook reads/writes."""
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    (tmp_path / "hooks" / "tests").mkdir(parents=True)
    (tmp_path / "hooks" / "_lib").mkdir(parents=True)
    (tmp_path / "generator" / "lib").mkdir(parents=True)
    (tmp_path / "generator" / "renderers").mkdir(parents=True)
    (tmp_path / "generator" / "__tests__").mkdir(parents=True)
    (tmp_path / "generator" / "__fixtures__").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "templates").mkdir(parents=True)
    return tmp_path


def touch(repo: Path, rel: str) -> Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()
    return p


# ---------------------------------------------------------------------------
# TestEnforcement — the core contract
# ---------------------------------------------------------------------------


class TestEnforcedHookNewFile:
    """hooks/<x>.py where file doesn't exist yet."""

    def test_without_test_pair_denies(self, repo: Path):
        result = run_hook(load_fixture("write_new_hook.json"), cwd=repo)
        assert result.returncode == 2
        out = parse_stdout(result)
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_with_test_pair_allows(self, repo: Path):
        touch(repo, "hooks/tests/test_new_guard.py")
        result = run_hook(load_fixture("write_new_hook.json"), cwd=repo)
        assert result.returncode == 0, result.stderr

    def test_deny_reason_points_at_expected_test_path(self, repo: Path):
        result = run_hook(load_fixture("write_new_hook.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "hooks/tests/test_new_guard.py" in reason
        assert "touch" in reason
        assert "CLAUDE.md" in reason
        assert "hooks/new_guard.py" in reason  # blocked write path echoed


class TestEnforcedHookExistingFile:
    """Edits/overwrites of an impl file that already exists → always allow,
    even when the test pair is missing. Keeps edit flow frictionless; D4
    pre-pr-gate is where missing coverage is caught."""

    def test_existing_impl_without_test_pair_allows(self, repo: Path):
        touch(repo, "hooks/new_guard.py")
        result = run_hook(load_fixture("write_new_hook.json"), cwd=repo)
        assert result.returncode == 0, result.stderr

    def test_existing_impl_with_test_pair_allows(self, repo: Path):
        touch(repo, "hooks/new_guard.py")
        touch(repo, "hooks/tests/test_new_guard.py")
        result = run_hook(load_fixture("write_new_hook.json"), cwd=repo)
        assert result.returncode == 0, result.stderr


class TestEnforcedGeneratorLib:
    def test_new_lib_without_test_pair_denies(self, repo: Path):
        result = run_hook(load_fixture("write_new_generator_lib.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "generator/lib/newmod.test.ts" in reason

    def test_new_lib_with_test_pair_allows(self, repo: Path):
        touch(repo, "generator/lib/newmod.test.ts")
        result = run_hook(load_fixture("write_new_generator_lib.json"), cwd=repo)
        assert result.returncode == 0, result.stderr

    def test_existing_lib_without_test_pair_allows(self, repo: Path):
        touch(repo, "generator/lib/newmod.ts")
        result = run_hook(load_fixture("write_new_generator_lib.json"), cwd=repo)
        assert result.returncode == 0, result.stderr


class TestEnforcedGeneratorRenderer:
    def test_new_renderer_without_test_pair_denies(self, repo: Path):
        result = run_hook(load_fixture("write_new_generator_renderer.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "generator/renderers/newrender.test.ts" in reason

    def test_new_renderer_with_test_pair_allows(self, repo: Path):
        touch(repo, "generator/renderers/newrender.test.ts")
        result = run_hook(load_fixture("write_new_generator_renderer.json"), cwd=repo)
        assert result.returncode == 0, result.stderr


class TestEnforcedGeneratorRunTs:
    """generator/run.ts is enforced (Fase -1 decision). Existing pair keeps
    it silently allowed today; ensuring the classifier treats it as enforced."""

    def test_new_run_ts_without_test_pair_denies(self, repo: Path):
        payload = make_write("generator/run.ts")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "generator/run.test.ts" in reason

    def test_new_run_ts_with_test_pair_allows(self, repo: Path):
        touch(repo, "generator/run.test.ts")
        payload = make_write("generator/run.ts")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# TestExclusions — path buckets that must pass-through silently (no log)
# ---------------------------------------------------------------------------


class TestExclusionsTestsDocsTemplatesMeta:
    """Category 1 exclusions: tests, docs, templates, meta / config."""

    def test_hook_test_file_passes_through(self, repo: Path):
        result = run_hook(load_fixture("write_hook_test_file.json"), cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_generator_tests_top_level_passes_through(self, repo: Path):
        payload = make_write("generator/__tests__/newcross.test.ts")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_generator_co_located_test_ts_passes_through(self, repo: Path):
        payload = make_write("generator/lib/something.test.ts")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_generator_fixtures_passes_through(self, repo: Path):
        payload = make_write("generator/__fixtures__/profile.yaml")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_docs_md_passes_through(self, repo: Path):
        payload = make_write("docs/NEWDOC.md")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_hbs_template_passes_through(self, repo: Path):
        payload = make_write("templates/NEW.md.hbs")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_yaml_passes_through(self, repo: Path):
        payload = make_write("questionnaire/schema.yaml")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_json_passes_through(self, repo: Path):
        payload = make_write(".claude/settings.json")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_snap_passes_through(self, repo: Path):
        payload = make_write("generator/renderers/__snapshots__/agents.test.ts.snap")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_hook_readme_passes_through(self, repo: Path):
        payload = make_write("hooks/README.md")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0


class TestExclusionsHelperInternals:
    """Category 2 exclusions: helper internals (hooks/_lib/**).

    Separate class on purpose — this is a deliberate repo decision
    (HANDOFF.md D2 notes) and is NOT equivalent to the tests/docs/meta bucket.
    """

    def test_hooks_lib_py_passes_through(self, repo: Path):
        result = run_hook(load_fixture("write_hooks_lib.json"), cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_hooks_lib_nested_py_passes_through(self, repo: Path):
        payload = make_write("hooks/_lib/subdir/deeper.py")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0


class TestOutOfScope:
    def test_non_write_tool_passes_through(self, repo: Path):
        result = run_hook(load_fixture("edit_non_write.json"), cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bash_tool_passes_through(self, repo: Path):
        payload = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_unrelated_path_passes_through(self, repo: Path):
        payload = make_write("tmp/scratch.txt")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_arbitrary_python_outside_hooks_passes_through(self, repo: Path):
        payload = make_write("scripts/helper.py")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_absolute_path_outside_repo_passes_through(self, repo: Path, tmp_path: Path):
        outside = tmp_path.parent / "elsewhere" / "foo.py"
        payload = make_write(str(outside))
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_absolute_path_inside_repo_enforced(self, repo: Path):
        payload = make_write(str(repo / "hooks" / "new_guard.py"))
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 2


# ---------------------------------------------------------------------------
# TestLogging — double-log only on decisions; zero log on pass-through
# ---------------------------------------------------------------------------


def _read_jsonl(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


class TestLogging:
    def test_deny_writes_both_logs(self, repo: Path):
        result = run_hook(load_fixture("write_new_hook.json"), cwd=repo)
        assert result.returncode == 2
        hook_log = repo / ".claude" / "logs" / "pre-write-guard.jsonl"
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        assert hook_log.exists()
        assert phase_log.exists()
        hook_entry = _read_jsonl(hook_log)[0]
        assert hook_entry["hook"] == "pre-write-guard"
        assert hook_entry["decision"] == "deny"
        assert hook_entry["file_path"].endswith("hooks/new_guard.py")
        assert "ts" in hook_entry
        assert "reason" in hook_entry
        phase_entry = _read_jsonl(phase_log)[0]
        assert phase_entry["event"] == "pre_write"
        assert phase_entry["decision"] == "deny"
        assert "ts" in phase_entry

    def test_allow_with_pair_writes_both_logs(self, repo: Path):
        touch(repo, "hooks/tests/test_new_guard.py")
        result = run_hook(load_fixture("write_new_hook.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-write-guard.jsonl"
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        assert hook_log.exists()
        assert phase_log.exists()
        assert _read_jsonl(hook_log)[-1]["decision"] == "allow"
        assert _read_jsonl(phase_log)[-1]["event"] == "pre_write"

    def test_allow_on_existing_file_writes_both_logs(self, repo: Path):
        """Edit flow on enforced path must still leave an audit trail."""
        touch(repo, "hooks/new_guard.py")
        result = run_hook(load_fixture("write_new_hook.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-write-guard.jsonl"
        assert hook_log.exists()
        entry = _read_jsonl(hook_log)[-1]
        assert entry["decision"] == "allow"

    def test_exclusion_does_not_log(self, repo: Path):
        result = run_hook(load_fixture("write_hooks_lib.json"), cwd=repo)
        assert result.returncode == 0
        assert not (repo / ".claude" / "logs" / "pre-write-guard.jsonl").exists()
        assert not (repo / ".claude" / "logs" / "phase-gates.jsonl").exists()

    def test_non_write_tool_does_not_log(self, repo: Path):
        result = run_hook(load_fixture("edit_non_write.json"), cwd=repo)
        assert result.returncode == 0
        assert not (repo / ".claude" / "logs" / "pre-write-guard.jsonl").exists()

    def test_out_of_scope_does_not_log(self, repo: Path):
        payload = make_write("scripts/helper.py")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0
        assert not (repo / ".claude" / "logs" / "pre-write-guard.jsonl").exists()

    def test_phase_gates_event_name_is_pre_write(self, repo: Path):
        result = run_hook(load_fixture("write_new_hook.json"), cwd=repo)
        assert result.returncode == 2
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        assert _read_jsonl(phase_log)[0]["event"] == "pre_write"


# ---------------------------------------------------------------------------
# TestRobustness — blocker safe-fail (D1 canonical, NOT D2 informative)
# ---------------------------------------------------------------------------


class TestRobustness:
    def test_malformed_json_denies(self, repo: Path):
        result = run_hook("not json{{{", cwd=repo)
        assert result.returncode == 2

    def test_empty_stdin_denies(self, repo: Path):
        result = run_hook("", cwd=repo)
        assert result.returncode == 2

    def test_non_dict_payload_denies(self, repo: Path):
        result = run_hook("[1,2,3]", cwd=repo)
        assert result.returncode == 2

    def test_tool_input_not_dict_denies(self, repo: Path):
        payload = {"tool_name": "Write", "tool_input": "bogus"}
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 2

    def test_missing_file_path_passes_through(self, repo: Path):
        payload = {"tool_name": "Write", "tool_input": {"content": "x"}}
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_file_path_not_string_passes_through(self, repo: Path):
        payload = {"tool_name": "Write", "tool_input": {"file_path": 42, "content": "x"}}
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_file_path_empty_passes_through(self, repo: Path):
        payload = make_write("")
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_idempotent_on_deny(self, repo: Path):
        r1 = run_hook(load_fixture("write_new_hook.json"), cwd=repo)
        r2 = run_hook(load_fixture("write_new_hook.json"), cwd=repo)
        assert r1.returncode == r2.returncode == 2
        entries = _read_jsonl(repo / ".claude" / "logs" / "pre-write-guard.jsonl")
        assert len(entries) == 2
        assert entries[0]["decision"] == entries[1]["decision"] == "deny"


# ---------------------------------------------------------------------------
# TestIsEnforcedUnit — classifier unit tests
# ---------------------------------------------------------------------------


class TestIsEnforcedUnit:
    # Enforced
    def test_hook_top_level_py_enforced(self):
        assert pwg.is_enforced("hooks/new_guard.py") is True

    def test_generator_lib_ts_enforced(self):
        assert pwg.is_enforced("generator/lib/foo.ts") is True

    def test_generator_lib_nested_ts_enforced(self):
        assert pwg.is_enforced("generator/lib/sub/deep.ts") is True

    def test_generator_renderer_ts_enforced(self):
        assert pwg.is_enforced("generator/renderers/foo.ts") is True

    def test_generator_run_ts_enforced(self):
        assert pwg.is_enforced("generator/run.ts") is True

    # Excluded by category 1 (tests/docs/templates/meta)
    def test_hook_tests_dir_excluded(self):
        assert pwg.is_enforced("hooks/tests/test_foo.py") is False

    def test_test_ts_excluded_at_lib(self):
        assert pwg.is_enforced("generator/lib/foo.test.ts") is False

    def test_test_ts_excluded_at_renderer(self):
        assert pwg.is_enforced("generator/renderers/foo.test.ts") is False

    def test_generator_top_tests_excluded(self):
        assert pwg.is_enforced("generator/__tests__/snapshots.test.ts") is False

    def test_generator_fixtures_excluded(self):
        assert pwg.is_enforced("generator/__fixtures__/profile.yaml") is False

    def test_md_excluded(self):
        assert pwg.is_enforced("hooks/README.md") is False

    def test_yaml_excluded(self):
        assert pwg.is_enforced("questionnaire/schema.yaml") is False

    def test_hbs_excluded(self):
        assert pwg.is_enforced("templates/X.md.hbs") is False

    # Excluded by category 2 (helper internals)
    def test_hooks_lib_excluded(self):
        assert pwg.is_enforced("hooks/_lib/slug.py") is False

    def test_hooks_lib_init_excluded(self):
        assert pwg.is_enforced("hooks/_lib/__init__.py") is False

    # Out of scope
    def test_non_hooks_py_out_of_scope(self):
        assert pwg.is_enforced("scripts/tool.py") is False

    def test_non_generator_ts_out_of_scope(self):
        assert pwg.is_enforced("unrelated/foo.ts") is False

    def test_hooks_deep_py_out_of_scope(self):
        # Non-_lib subdir under hooks is not enforced (we only require
        # test-pair for top-level hooks/*.py; anything deeper has no
        # declared pair convention).
        assert pwg.is_enforced("hooks/other/thing.py") is False


class TestExpectedTestPairUnit:
    def test_hook_py(self):
        assert pwg.expected_test_pair("hooks/pre-write-guard.py") == \
            "hooks/tests/test_pre_write_guard.py"

    def test_hook_py_underscore_preserved(self):
        assert pwg.expected_test_pair("hooks/already_under.py") == \
            "hooks/tests/test_already_under.py"

    def test_generator_lib_ts(self):
        assert pwg.expected_test_pair("generator/lib/foo.ts") == \
            "generator/lib/foo.test.ts"

    def test_generator_renderer_ts(self):
        assert pwg.expected_test_pair("generator/renderers/bar.ts") == \
            "generator/renderers/bar.test.ts"

    def test_generator_lib_nested_ts(self):
        assert pwg.expected_test_pair("generator/lib/sub/deep.ts") == \
            "generator/lib/sub/deep.test.ts"

    def test_generator_run_ts(self):
        assert pwg.expected_test_pair("generator/run.ts") == \
            "generator/run.test.ts"


class TestBuildDenyReasonUnit:
    def test_contains_expected_path_touch_rule_and_blocked_write(self):
        reason = pwg.build_deny_reason(
            write_path="hooks/new_guard.py",
            expected_test="hooks/tests/test_new_guard.py",
        )
        assert "hooks/tests/test_new_guard.py" in reason
        assert "touch" in reason
        assert "CLAUDE.md" in reason
        assert "hooks/new_guard.py" in reason


# ---------------------------------------------------------------------------
# TestMainInProcess — coverage paths unreachable via subprocess
# ---------------------------------------------------------------------------


class TestMainInProcess:
    def _run(
        self,
        monkeypatch: pytest.MonkeyPatch,
        repo: Path,
        stdin_text: str,
    ) -> int:
        monkeypatch.chdir(repo)
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
        return pwg.main()

    def test_malformed_json_returns_2(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, "not json") == 2

    def test_non_dict_payload_returns_2(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, "[1,2,3]") == 2

    def test_non_write_returns_0(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, '{"tool_name": "Bash"}') == 0

    def test_write_no_tool_input_returns_0(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, '{"tool_name": "Write"}') == 0

    def test_write_null_tool_input_returns_0(self, monkeypatch, repo):
        payload = '{"tool_name": "Write", "tool_input": null}'
        assert self._run(monkeypatch, repo, payload) == 0

    def test_write_list_tool_input_returns_2(self, monkeypatch, repo):
        payload = '{"tool_name": "Write", "tool_input": [1,2]}'
        assert self._run(monkeypatch, repo, payload) == 2

    def test_write_missing_file_path_returns_0(self, monkeypatch, repo):
        payload = '{"tool_name": "Write", "tool_input": {"content": "x"}}'
        assert self._run(monkeypatch, repo, payload) == 0

    def test_write_enforced_new_no_pair_returns_2(self, monkeypatch, repo):
        payload = json.dumps(make_write("hooks/new_guard.py"))
        assert self._run(monkeypatch, repo, payload) == 2

    def test_write_enforced_new_with_pair_returns_0(self, monkeypatch, repo):
        touch(repo, "hooks/tests/test_new_guard.py")
        payload = json.dumps(make_write("hooks/new_guard.py"))
        assert self._run(monkeypatch, repo, payload) == 0

    def test_write_enforced_existing_file_returns_0(self, monkeypatch, repo):
        touch(repo, "hooks/new_guard.py")
        payload = json.dumps(make_write("hooks/new_guard.py"))
        assert self._run(monkeypatch, repo, payload) == 0

    def test_write_excluded_returns_0(self, monkeypatch, repo):
        payload = json.dumps(make_write("hooks/_lib/helper.py"))
        assert self._run(monkeypatch, repo, payload) == 0

    def test_write_out_of_scope_returns_0(self, monkeypatch, repo):
        payload = json.dumps(make_write("scripts/tool.py"))
        assert self._run(monkeypatch, repo, payload) == 0

    def test_write_absolute_inside_repo_enforced(self, monkeypatch, repo):
        abs_path = str(repo / "hooks" / "new_guard.py")
        payload = json.dumps(make_write(abs_path))
        assert self._run(monkeypatch, repo, payload) == 2

    def test_write_absolute_outside_repo_returns_0(self, monkeypatch, repo, tmp_path):
        abs_path = str(tmp_path.parent / "elsewhere" / "foo.py")
        payload = json.dumps(make_write(abs_path))
        assert self._run(monkeypatch, repo, payload) == 0

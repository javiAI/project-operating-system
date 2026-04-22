"""Tests for hooks/pre-compact.py — sixth hook (D6), PreCompact informative.

Shape: D2 informative (never blocker). Exit 0 always, never emits
`permissionDecision`. Reads `pre_compact_rules()` from the loader and emits
`additionalContext` listing persist items so the model persists them before
the compact.

Failure mode (c.2): accessor None → minimal additionalContext +
`status: policy_unavailable` log. Never deny blind.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "hooks" / "pre-compact.py"
FIXTURES = Path(__file__).parent / "fixtures" / "payloads"
POLICY_FIXTURES = Path(__file__).parent / "fixtures" / "policy"

_spec = importlib.util.spec_from_file_location("pre_compact", HOOK)
assert _spec is not None and _spec.loader is not None
pc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pc)


def run_hook(payload, cwd: Path) -> subprocess.CompletedProcess:
    stdin = json.dumps(payload) if isinstance(payload, (dict, list)) else payload
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=5,
    )


def load_payload(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def parse_stdout(result: subprocess.CompletedProcess) -> dict:
    return json.loads(result.stdout) if result.stdout.strip() else {}


def additional_context(result: subprocess.CompletedProcess) -> str:
    return parse_stdout(result)["hookSpecificOutput"]["additionalContext"]


@pytest.fixture(autouse=True)
def clear_cache():
    from _lib import policy as pol
    pol.reset_cache()
    yield
    pol.reset_cache()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Fresh tmp repo root with logs dir + full policy fixture."""
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    src = POLICY_FIXTURES / "full.yaml"
    (tmp_path / "policy.yaml").write_text(src.read_text(encoding="utf-8"),
                                          encoding="utf-8")
    return tmp_path


@pytest.fixture
def repo_no_policy(tmp_path: Path) -> Path:
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    return tmp_path


def read_log(repo: Path, name: str) -> list[dict]:
    log = repo / ".claude" / "logs" / name
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]


# ─────────────────────────────────────────────────────────────────────────────
# Output envelope — informative shape (D2, exit 0 always)
# ─────────────────────────────────────────────────────────────────────────────


class TestOutputEnvelope:
    def test_always_exits_zero_on_happy_path(self, repo: Path):
        result = run_hook(load_payload("pre_compact_auto.json"), cwd=repo)
        assert result.returncode == 0, result.stderr

    def test_hook_event_name_is_pre_compact(self, repo: Path):
        result = run_hook(load_payload("pre_compact_auto.json"), cwd=repo)
        out = parse_stdout(result)
        assert out["hookSpecificOutput"]["hookEventName"] == "PreCompact"

    def test_never_emits_permission_decision(self, repo: Path):
        result = run_hook(load_payload("pre_compact_auto.json"), cwd=repo)
        out = parse_stdout(result)
        assert "permissionDecision" not in out["hookSpecificOutput"]

    def test_additional_context_is_string(self, repo: Path):
        result = run_hook(load_payload("pre_compact_auto.json"), cwd=repo)
        ctx = additional_context(result)
        assert isinstance(ctx, str)
        assert ctx.strip() != ""


# ─────────────────────────────────────────────────────────────────────────────
# Happy path — emits persist checklist from policy
# ─────────────────────────────────────────────────────────────────────────────


class TestHappyPath:
    def test_lists_all_persist_items(self, repo: Path):
        result = run_hook(load_payload("pre_compact_auto.json"), cwd=repo)
        ctx = additional_context(result)
        assert "decisions_in_flight" in ctx
        assert "phase_minus_one_state" in ctx
        assert "unsaved_pattern_candidates" in ctx

    def test_mentions_pre_compact_purpose(self, repo: Path):
        result = run_hook(load_payload("pre_compact_auto.json"), cwd=repo)
        ctx = additional_context(result)
        # Must be a reminder to persist — not opaque metadata.
        assert "persist" in ctx.lower() or "preserve" in ctx.lower()

    def test_auto_and_manual_triggers_produce_same_output(self, repo: Path):
        auto = additional_context(run_hook(load_payload("pre_compact_auto.json"), cwd=repo))
        manual = additional_context(run_hook(load_payload("pre_compact_manual.json"), cwd=repo))
        assert auto == manual


# ─────────────────────────────────────────────────────────────────────────────
# Failure mode (c.2) — loader None → minimal context + policy_unavailable log
# ─────────────────────────────────────────────────────────────────────────────


class TestFailureMode:
    def test_missing_policy_does_not_block(self, repo_no_policy: Path):
        result = run_hook(load_payload("pre_compact_auto.json"), cwd=repo_no_policy)
        assert result.returncode == 0, result.stderr

    def test_missing_policy_emits_minimal_context(self, repo_no_policy: Path):
        result = run_hook(load_payload("pre_compact_auto.json"), cwd=repo_no_policy)
        ctx = additional_context(result)
        assert "policy" in ctx.lower()
        assert "unavailable" in ctx.lower() or "missing" in ctx.lower()

    def test_missing_policy_logs_status(self, repo_no_policy: Path):
        run_hook(load_payload("pre_compact_auto.json"), cwd=repo_no_policy)
        entries = read_log(repo_no_policy, "pre-compact.jsonl")
        assert any(e.get("status") == "policy_unavailable" for e in entries)

    def test_malformed_policy_does_not_block(self, tmp_path: Path):
        (tmp_path / ".claude" / "logs").mkdir(parents=True)
        (tmp_path / "policy.yaml").write_text("key: [broken\n", encoding="utf-8")
        result = run_hook(load_payload("pre_compact_auto.json"), cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        entries = read_log(tmp_path, "pre-compact.jsonl")
        assert any(e.get("status") == "policy_unavailable" for e in entries)

    def test_policy_without_pre_compact_section(self, tmp_path: Path):
        (tmp_path / ".claude" / "logs").mkdir(parents=True)
        (tmp_path / "policy.yaml").write_text(
            "version: \"0.1.0\"\nproject: \"x\"\n", encoding="utf-8"
        )
        result = run_hook(load_payload("pre_compact_auto.json"), cwd=tmp_path)
        assert result.returncode == 0
        entries = read_log(tmp_path, "pre-compact.jsonl")
        assert any(e.get("status") == "policy_unavailable" for e in entries)


# ─────────────────────────────────────────────────────────────────────────────
# Safe-fail informative — malformed payload NEVER blocks
# ─────────────────────────────────────────────────────────────────────────────


class TestSafeFailInformative:
    def test_empty_stdin_exits_zero(self, repo: Path):
        result = run_hook("", cwd=repo)
        assert result.returncode == 0, result.stderr

    def test_empty_stdin_emits_minimal_context(self, repo: Path):
        result = run_hook("", cwd=repo)
        ctx = additional_context(result)
        assert isinstance(ctx, str)

    def test_invalid_json_exits_zero(self, repo: Path):
        result = run_hook("{not-json", cwd=repo)
        assert result.returncode == 0

    def test_invalid_json_emits_context(self, repo: Path):
        result = run_hook("{not-json", cwd=repo)
        ctx = additional_context(result)
        assert "error" in ctx.lower() or "malformed" in ctx.lower()

    def test_top_level_list_exits_zero(self, repo: Path):
        result = run_hook([1, 2, 3], cwd=repo)
        assert result.returncode == 0

    def test_top_level_scalar_exits_zero(self, repo: Path):
        result = run_hook("42", cwd=repo)
        assert result.returncode == 0

    def test_never_emits_permission_decision_on_bad_payload(self, repo: Path):
        result = run_hook("{broken", cwd=repo)
        out = parse_stdout(result)
        assert "permissionDecision" not in out.get("hookSpecificOutput", {})


# ─────────────────────────────────────────────────────────────────────────────
# Logging — double log (hook log + phase-gates) on real decisions
# ─────────────────────────────────────────────────────────────────────────────


class TestLogging:
    def test_hook_log_written_on_happy_path(self, repo: Path):
        run_hook(load_payload("pre_compact_auto.json"), cwd=repo)
        entries = read_log(repo, "pre-compact.jsonl")
        assert len(entries) >= 1
        assert any(e.get("hook") == "pre-compact" for e in entries)

    def test_phase_gates_event_pre_compact(self, repo: Path):
        run_hook(load_payload("pre_compact_auto.json"), cwd=repo)
        entries = read_log(repo, "phase-gates.jsonl")
        assert any(e.get("event") == "pre_compact" for e in entries)

    def test_trigger_recorded_in_log(self, repo: Path):
        run_hook(load_payload("pre_compact_manual.json"), cwd=repo)
        entries = read_log(repo, "pre-compact.jsonl")
        assert any(e.get("trigger") == "manual" for e in entries)


# ─────────────────────────────────────────────────────────────────────────────
# In-process tests — coverage of policy/git paths via module invocation
# ─────────────────────────────────────────────────────────────────────────────


class TestMainInProcess:
    """Load the hook module and call main() with monkeypatched stdin."""

    def _run(self, monkeypatch, cwd: Path, payload) -> tuple[int, str]:
        import io as _io
        stdin = json.dumps(payload) if isinstance(payload, (dict, list)) else payload
        monkeypatch.setattr("sys.stdin", _io.StringIO(stdin))
        monkeypatch.chdir(cwd)
        captured = _io.StringIO()
        monkeypatch.setattr("sys.stdout", captured)
        rc = pc.main()
        return rc, captured.getvalue()

    def test_happy_path(self, repo: Path, monkeypatch):
        rc, out = self._run(monkeypatch, repo, {"hook_event_name": "PreCompact",
                                                 "trigger": "auto"})
        assert rc == 0
        data = json.loads(out)
        assert data["hookSpecificOutput"]["hookEventName"] == "PreCompact"

    def test_missing_policy_in_process(self, repo_no_policy: Path, monkeypatch):
        rc, out = self._run(monkeypatch, repo_no_policy,
                            {"hook_event_name": "PreCompact", "trigger": "auto"})
        assert rc == 0
        data = json.loads(out)
        assert "policy" in data["hookSpecificOutput"]["additionalContext"].lower()

    def test_bad_stdin_in_process(self, repo: Path, monkeypatch):
        rc, out = self._run(monkeypatch, repo, "{bad")
        assert rc == 0
        data = json.loads(out)
        assert "permissionDecision" not in data.get("hookSpecificOutput", {})

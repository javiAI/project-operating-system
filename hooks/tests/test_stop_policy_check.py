"""Tests for hooks/stop-policy-check.py — seventh hook (D6), Stop blocker-scaffold.

Framing (aprobado Fase -1):
  - Shape D1 blocker: safe-fail denies on malformed payload; permissionDecision
    available; enforcement live when `skills_allowed` is declared in policy.yaml.
  - TODAY enforcement is DEFERRED — `policy.yaml.skills_allowed` does not exist
    in the meta-repo yet, so the hook degrades to `status: deferred` log +
    pass-through (exit 0). Real enforcement activates when E1a (or later) adds
    the `skills_allowed` key — no code refactor needed.
  - Tests fixture-write `skills_allowed: [...]` to exercise the activable path
    end-to-end (deny when a skill is outside the allowlist). These are
    future-proof tests, not prod enforcement today.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "hooks" / "stop-policy-check.py"
FIXTURES = Path(__file__).parent / "fixtures" / "payloads"
POLICY_FIXTURES = Path(__file__).parent / "fixtures" / "policy"

_spec = importlib.util.spec_from_file_location("stop_policy_check", HOOK)
assert _spec is not None and _spec.loader is not None
sp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sp)


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


@pytest.fixture(autouse=True)
def clear_cache():
    from _lib import policy as pol
    pol.reset_cache()
    yield
    pol.reset_cache()


@pytest.fixture
def repo_no_policy(tmp_path: Path) -> Path:
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def repo_full_policy(tmp_path: Path) -> Path:
    """Repo with the `full.yaml` fixture (declares skills_allowed)."""
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    src = POLICY_FIXTURES / "full.yaml"
    (tmp_path / "policy.yaml").write_text(src.read_text(encoding="utf-8"),
                                          encoding="utf-8")
    return tmp_path


@pytest.fixture
def repo_no_skills_section(tmp_path: Path) -> Path:
    """Policy exists but lacks skills_allowed (prod state today)."""
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    (tmp_path / "policy.yaml").write_text(
        "version: \"0.1.0\"\nproject: \"x\"\ntype: \"meta-repo\"\n",
        encoding="utf-8",
    )
    return tmp_path


def write_skills_allowed(repo: Path, allowed: list[str]) -> None:
    """Replace policy.yaml with one that only declares skills_allowed."""
    import yaml as _yaml
    (repo / "policy.yaml").write_text(
        _yaml.safe_dump({"skills_allowed": allowed}, sort_keys=False),
        encoding="utf-8",
    )


def seed_skills_log(repo: Path, skills: list[str]) -> None:
    """Write `.claude/logs/skills.jsonl` with one entry per skill name."""
    log = repo / ".claude" / "logs" / "skills.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as f:
        for name in skills:
            f.write(json.dumps({"skill": name}) + "\n")


def read_log(repo: Path, name: str) -> list[dict]:
    log = repo / ".claude" / "logs" / name
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]


# ─────────────────────────────────────────────────────────────────────────────
# Output envelope
# ─────────────────────────────────────────────────────────────────────────────


class TestOutputEnvelope:
    def test_hook_event_name_on_deny(self, repo_full_policy: Path):
        """When enforcement denies, envelope exposes Stop + deny shape."""
        write_skills_allowed(repo_full_policy, ["pos:kickoff"])
        seed_skills_log(repo_full_policy, ["pos:rogue"])
        result = run_hook(load_payload("stop.json"), cwd=repo_full_policy)
        assert result.returncode == 2
        out = parse_stdout(result)
        assert out["hookSpecificOutput"]["hookEventName"] == "Stop"
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_exit_code_is_zero_when_allow_or_deferred(self, repo_no_policy: Path):
        result = run_hook(load_payload("stop.json"), cwd=repo_no_policy)
        assert result.returncode == 0


# ─────────────────────────────────────────────────────────────────────────────
# Deferred mode (production today)
# ─────────────────────────────────────────────────────────────────────────────


class TestDeferredMode:
    def test_missing_policy_is_pass_through(self, repo_no_policy: Path):
        result = run_hook(load_payload("stop.json"), cwd=repo_no_policy)
        assert result.returncode == 0
        entries = read_log(repo_no_policy, "stop-policy-check.jsonl")
        assert any(e.get("status") == "policy_unavailable" for e in entries)

    def test_missing_policy_does_not_emit_decision(self, repo_no_policy: Path):
        result = run_hook(load_payload("stop.json"), cwd=repo_no_policy)
        out = parse_stdout(result)
        # Pass-through emits no JSON body (consistent with D1 pass-through).
        assert "permissionDecision" not in out.get("hookSpecificOutput", {})

    def test_policy_without_skills_allowed_is_deferred(self,
                                                       repo_no_skills_section: Path):
        result = run_hook(load_payload("stop.json"), cwd=repo_no_skills_section)
        assert result.returncode == 0
        entries = read_log(repo_no_skills_section, "stop-policy-check.jsonl")
        assert any(e.get("status") == "deferred" for e in entries)

    def test_deferred_never_blocks_user(self, repo_no_skills_section: Path):
        """Framing contract: deferred mode must not block ever."""
        result = run_hook(load_payload("stop.json"), cwd=repo_no_skills_section)
        assert result.returncode == 0
        out = parse_stdout(result)
        assert "permissionDecision" not in out.get("hookSpecificOutput", {})


# ─────────────────────────────────────────────────────────────────────────────
# Activable enforcement (future-proof tests, live when skills_allowed declared)
# ─────────────────────────────────────────────────────────────────────────────


class TestActivableEnforcement:
    def test_empty_allowlist_plus_no_skills_invoked_allows(self,
                                                           repo_full_policy: Path):
        write_skills_allowed(repo_full_policy, [])
        # no skills.jsonl → zero invocations → no violations
        result = run_hook(load_payload("stop.json"), cwd=repo_full_policy)
        assert result.returncode == 0

    def test_empty_allowlist_plus_any_skill_denies(self, repo_full_policy: Path):
        write_skills_allowed(repo_full_policy, [])
        seed_skills_log(repo_full_policy, ["pos:kickoff"])
        result = run_hook(load_payload("stop.json"), cwd=repo_full_policy)
        assert result.returncode == 2
        out = parse_stdout(result)
        reason = out["hookSpecificOutput"]["decisionReason"]
        assert "pos:kickoff" in reason

    def test_skill_in_allowlist_allows(self, repo_full_policy: Path):
        write_skills_allowed(repo_full_policy, ["pos:kickoff"])
        seed_skills_log(repo_full_policy, ["pos:kickoff"])
        result = run_hook(load_payload("stop.json"), cwd=repo_full_policy)
        assert result.returncode == 0

    def test_skill_not_in_allowlist_denies(self, repo_full_policy: Path):
        write_skills_allowed(repo_full_policy, ["pos:kickoff"])
        seed_skills_log(repo_full_policy, ["pos:rogue"])
        result = run_hook(load_payload("stop.json"), cwd=repo_full_policy)
        assert result.returncode == 2
        out = parse_stdout(result)
        reason = out["hookSpecificOutput"]["decisionReason"]
        assert "pos:rogue" in reason
        assert "skills_allowed" in reason or "allowlist" in reason.lower()

    def test_mixed_invocations_denies_on_first_violation(self,
                                                         repo_full_policy: Path):
        write_skills_allowed(repo_full_policy, ["pos:kickoff"])
        seed_skills_log(repo_full_policy, ["pos:kickoff", "pos:rogue"])
        result = run_hook(load_payload("stop.json"), cwd=repo_full_policy)
        assert result.returncode == 2
        out = parse_stdout(result)
        assert "pos:rogue" in out["hookSpecificOutput"]["decisionReason"]

    def test_no_skills_log_is_treated_as_no_invocations(self,
                                                        repo_full_policy: Path):
        write_skills_allowed(repo_full_policy, ["pos:kickoff"])
        # No skills.jsonl file; nothing was invoked.
        result = run_hook(load_payload("stop.json"), cwd=repo_full_policy)
        assert result.returncode == 0

    def test_corrupt_skills_log_does_not_crash(self, repo_full_policy: Path):
        write_skills_allowed(repo_full_policy, ["pos:kickoff"])
        log = repo_full_policy / ".claude" / "logs" / "skills.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("not-json\n{also-broken\n", encoding="utf-8")
        result = run_hook(load_payload("stop.json"), cwd=repo_full_policy)
        # Robustness: corrupt lines → ignored, not crash.
        assert result.returncode in (0, 2)


# ─────────────────────────────────────────────────────────────────────────────
# Safe-fail blocker canonical (D1): malformed payload → deny exit 2
# ─────────────────────────────────────────────────────────────────────────────


class TestSafeFailBlocker:
    def test_empty_stdin_denies(self, repo_no_policy: Path):
        result = run_hook("", cwd=repo_no_policy)
        assert result.returncode == 2
        out = parse_stdout(result)
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_invalid_json_denies(self, repo_no_policy: Path):
        result = run_hook("{not-json", cwd=repo_no_policy)
        assert result.returncode == 2

    def test_top_level_list_denies(self, repo_no_policy: Path):
        result = run_hook([1, 2, 3], cwd=repo_no_policy)
        assert result.returncode == 2

    def test_top_level_scalar_denies(self, repo_no_policy: Path):
        result = run_hook("42", cwd=repo_no_policy)
        assert result.returncode == 2


# ─────────────────────────────────────────────────────────────────────────────
# Logging — double log on real decisions
# ─────────────────────────────────────────────────────────────────────────────


class TestLogging:
    def test_deferred_logs_only_to_hook_log(self, repo_no_skills_section: Path):
        """Deferred status does NOT cross into phase-gates.jsonl."""
        run_hook(load_payload("stop.json"), cwd=repo_no_skills_section)
        hook_log = read_log(repo_no_skills_section, "stop-policy-check.jsonl")
        phase_log = read_log(repo_no_skills_section, "phase-gates.jsonl")
        assert any(e.get("status") == "deferred" for e in hook_log)
        assert phase_log == []

    def test_deny_logs_to_both(self, repo_full_policy: Path):
        write_skills_allowed(repo_full_policy, ["pos:kickoff"])
        seed_skills_log(repo_full_policy, ["pos:rogue"])
        run_hook(load_payload("stop.json"), cwd=repo_full_policy)
        hook_log = read_log(repo_full_policy, "stop-policy-check.jsonl")
        phase_log = read_log(repo_full_policy, "phase-gates.jsonl")
        assert any(e.get("decision") == "deny" for e in hook_log)
        assert any(e.get("event") == "stop" and e.get("decision") == "deny"
                   for e in phase_log)

    def test_allow_logs_to_both(self, repo_full_policy: Path):
        write_skills_allowed(repo_full_policy, ["pos:kickoff"])
        seed_skills_log(repo_full_policy, ["pos:kickoff"])
        run_hook(load_payload("stop.json"), cwd=repo_full_policy)
        hook_log = read_log(repo_full_policy, "stop-policy-check.jsonl")
        phase_log = read_log(repo_full_policy, "phase-gates.jsonl")
        assert any(e.get("decision") == "allow" for e in hook_log)
        assert any(e.get("event") == "stop" and e.get("decision") == "allow"
                   for e in phase_log)


# ─────────────────────────────────────────────────────────────────────────────
# In-process tests — coverage of policy/skills-log paths
# ─────────────────────────────────────────────────────────────────────────────


class TestMainInProcess:
    def _run(self, monkeypatch, cwd: Path, payload) -> tuple[int, str]:
        import io as _io
        stdin = json.dumps(payload) if isinstance(payload, (dict, list)) else payload
        monkeypatch.setattr("sys.stdin", _io.StringIO(stdin))
        monkeypatch.chdir(cwd)
        captured = _io.StringIO()
        monkeypatch.setattr("sys.stdout", captured)
        rc = sp.main()
        return rc, captured.getvalue()

    def test_missing_policy_returns_zero(self, repo_no_policy: Path, monkeypatch):
        rc, _ = self._run(monkeypatch, repo_no_policy,
                          {"hook_event_name": "Stop"})
        assert rc == 0

    def test_deferred_returns_zero(self, repo_no_skills_section: Path, monkeypatch):
        rc, _ = self._run(monkeypatch, repo_no_skills_section,
                          {"hook_event_name": "Stop"})
        assert rc == 0

    def test_deny_returns_two(self, repo_full_policy: Path, monkeypatch):
        write_skills_allowed(repo_full_policy, ["pos:kickoff"])
        seed_skills_log(repo_full_policy, ["pos:rogue"])
        rc, out = self._run(monkeypatch, repo_full_policy,
                            {"hook_event_name": "Stop"})
        assert rc == 2
        data = json.loads(out)
        assert data["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_allow_returns_zero(self, repo_full_policy: Path, monkeypatch):
        write_skills_allowed(repo_full_policy, ["pos:kickoff"])
        seed_skills_log(repo_full_policy, ["pos:kickoff"])
        rc, _ = self._run(monkeypatch, repo_full_policy,
                          {"hook_event_name": "Stop"})
        assert rc == 0

    def test_bad_stdin_denies_in_process(self, repo_no_policy: Path, monkeypatch):
        rc, out = self._run(monkeypatch, repo_no_policy, "{bad")
        assert rc == 2
        data = json.loads(out)
        assert data["hookSpecificOutput"]["permissionDecision"] == "deny"


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests — extractor + validator (isolated, no subprocess)
# ─────────────────────────────────────────────────────────────────────────────


class TestExtractInvokedSkillsUnit:
    def test_missing_log_returns_empty(self, tmp_path: Path):
        assert sp._extract_invoked_skills(tmp_path) == []

    def test_single_skill(self, tmp_path: Path):
        (tmp_path / ".claude" / "logs").mkdir(parents=True)
        (tmp_path / ".claude" / "logs" / "skills.jsonl").write_text(
            json.dumps({"skill": "pos:kickoff"}) + "\n", encoding="utf-8"
        )
        assert sp._extract_invoked_skills(tmp_path) == ["pos:kickoff"]

    def test_ignores_lines_without_skill_key(self, tmp_path: Path):
        (tmp_path / ".claude" / "logs").mkdir(parents=True)
        (tmp_path / ".claude" / "logs" / "skills.jsonl").write_text(
            json.dumps({"other": "x"}) + "\n" +
            json.dumps({"skill": "pos:kickoff"}) + "\n",
            encoding="utf-8",
        )
        assert sp._extract_invoked_skills(tmp_path) == ["pos:kickoff"]

    def test_ignores_corrupt_lines(self, tmp_path: Path):
        (tmp_path / ".claude" / "logs").mkdir(parents=True)
        (tmp_path / ".claude" / "logs" / "skills.jsonl").write_text(
            "not-json\n" + json.dumps({"skill": "pos:kickoff"}) + "\n",
            encoding="utf-8",
        )
        assert sp._extract_invoked_skills(tmp_path) == ["pos:kickoff"]

    def test_ignores_non_string_skill(self, tmp_path: Path):
        (tmp_path / ".claude" / "logs").mkdir(parents=True)
        (tmp_path / ".claude" / "logs" / "skills.jsonl").write_text(
            json.dumps({"skill": 42}) + "\n", encoding="utf-8"
        )
        assert sp._extract_invoked_skills(tmp_path) == []


class TestValidateSkillsUnit:
    def test_empty_invoked_is_allow(self):
        decision, violations = sp._validate([], ("pos:kickoff",))
        assert decision == "allow"
        assert violations == []

    def test_all_invoked_in_allowlist(self):
        decision, _ = sp._validate(["pos:kickoff"], ("pos:kickoff",))
        assert decision == "allow"

    def test_violation_detected(self):
        decision, violations = sp._validate(
            ["pos:kickoff", "pos:rogue"], ("pos:kickoff",)
        )
        assert decision == "deny"
        assert violations == ["pos:rogue"]

    def test_empty_allowlist_denies_any_invocation(self):
        decision, violations = sp._validate(["pos:kickoff"], ())
        assert decision == "deny"
        assert violations == ["pos:kickoff"]

    def test_empty_invoked_empty_allowlist_allows(self):
        decision, _ = sp._validate([], ())
        assert decision == "allow"

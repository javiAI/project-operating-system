"""Tests for hooks/pre-pr-gate.py.

D4 blocker hook — enforces docs-sync on `gh pr create`. See CLAUDE.md regla #2
and policy.yaml.lifecycle.pre_pr.docs_sync_required/docs_sync_conditional
(mirrored as hardcoded rules in the hook; migration to policy-driven loading
deferred to a dedicated rama alongside D3 path migration).

Crystal-clear contract this suite locks in:
- `gh pr create` + docs-sync missing                → deny (exit 2)
- `gh pr create` + docs-sync satisfied              → allow (exit 0, double log)
- `gh pr create` + empty diff vs merge-base         → deny "empty PR" (NOT docs-sync)
- `gh pr create` + on main/master/detached HEAD     → pass-through + advisory log
- `gh pr create` + git unavailable / merge-base NA  → pass-through + advisory log
- Non-Bash or non-gh-pr-create command              → pass-through silent (no log)
- Malformed stdin / payload / tool_input            → deny exit 2 (blocker safe-fail)
- Every gated invocation (allow+deny) emits 3 deferred advisory entries
  (skills_required, ci_dry_run_required, invariants_check) — NOT emitted on
  skip/pass-through.

Shape identical to D1 (blocker), NOT D2 (informative).
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
HOOK = REPO_ROOT / "hooks" / "pre-pr-gate.py"
FIXTURES = Path(__file__).parent / "fixtures" / "payloads"

_HOOK_EXISTS = HOOK.exists()
if _HOOK_EXISTS:
    _spec = importlib.util.spec_from_file_location("pre_pr_gate", HOOK)
    assert _spec is not None and _spec.loader is not None
    ppg = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ppg)
else:
    ppg = None


needs_hook = pytest.mark.skipif(
    not _HOOK_EXISTS, reason="hook not yet implemented (RED kickoff state)"
)


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


def make_bash(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def _git(cwd: Path, *args: str) -> str:
    """Run git in cwd; raise on non-zero. For fixture setup only, not hook logic."""
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
    )
    return result.stdout


POLICY_YAML_FOR_TESTS = """\
lifecycle:
  pre_pr:
    docs_sync_required:
      - "ROADMAP.md"
      - "HANDOFF.md"
    docs_sync_conditional:
      - if_touched: ["generator/**"]
        then_required: ["docs/ARCHITECTURE.md"]
      - if_touched: ["hooks/**"]
        then_required: ["docs/ARCHITECTURE.md"]
        excludes: ["hooks/tests/**"]
      - if_touched: ["skills/**"]
        then_required: [".claude/rules/skills-map.md"]
      - if_touched: [".claude/patterns/**"]
        then_required: ["docs/ARCHITECTURE.md"]
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Real git repo: main branch + initial commit + .claude/logs + policy.yaml."""
    _git(tmp_path, "init", "-q", "--initial-branch=main")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("initial\n")
    (tmp_path / "policy.yaml").write_text(POLICY_YAML_FOR_TESTS)
    _git(tmp_path, "add", "README.md", "policy.yaml")
    _git(tmp_path, "commit", "-q", "-m", "initial")
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    return tmp_path


@pytest.fixture(autouse=True)
def _reset_policy_cache():
    """Isolate loader cache between tests (different tmp_path each test)."""
    sys.path.insert(0, str(REPO_ROOT / "hooks"))
    from _lib.policy import reset_cache
    reset_cache()
    yield
    reset_cache()


def checkout(repo: Path, branch: str) -> None:
    _git(repo, "checkout", "-q", "-b", branch)


def commit(repo: Path, msg: str, **files: str) -> None:
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        _git(repo, "add", rel)
    _git(repo, "commit", "-q", "-m", msg)


def _read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# TestMatcherDetection — which commands trigger the gate
# ---------------------------------------------------------------------------


class TestMatcherDetection:
    def test_gh_pr_create_triggers_gate(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2

    def test_gh_pr_create_draft_triggers_gate(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        result = run_hook(load_fixture("gh_pr_create_draft.json"), cwd=repo)
        assert result.returncode == 2

    def test_gh_pr_create_with_title_triggers_gate(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        result = run_hook(make_bash('gh pr create --title "D4 hook"'), cwd=repo)
        assert result.returncode == 2

    def test_gh_pr_create_with_base_flag_triggers_gate(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        result = run_hook(make_bash("gh pr create --base main"), cwd=repo)
        assert result.returncode == 2

    def test_gh_pr_create_with_body_triggers_gate(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        result = run_hook(make_bash('gh pr create --body "desc"'), cwd=repo)
        assert result.returncode == 2

    def test_gh_pr_list_passes_through(self, repo: Path):
        result = run_hook(load_fixture("gh_pr_list.json"), cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_gh_pr_view_passes_through(self, repo: Path):
        result = run_hook(make_bash("gh pr view 123"), cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_gh_issue_create_passes_through(self, repo: Path):
        """gh issue create is NOT gh pr create; must pass-through."""
        result = run_hook(make_bash("gh issue create"), cwd=repo)
        assert result.returncode == 0

    def test_git_status_passes_through(self, repo: Path):
        result = run_hook(load_fixture("git_status.json"), cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_git_push_passes_through(self, repo: Path):
        """Deferred matcher: git push is NOT gated by D4 (documented deferral)."""
        result = run_hook(make_bash("git push origin HEAD"), cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_non_bash_tool_passes_through(self, repo: Path):
        result = run_hook(load_fixture("non_bash.json"), cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""


# ---------------------------------------------------------------------------
# TestBranchSkip — main / master / detached HEAD → advisory, not gated
# ---------------------------------------------------------------------------


class TestBranchSkip:
    def test_on_main_passes_through_with_advisory_log(self, repo: Path):
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        assert hook_log.exists()
        assert not phase_log.exists()
        entries = _read_jsonl(hook_log)
        assert any(
            e.get("status") == "skipped" and "main" in e.get("reason", "").lower()
            for e in entries
        )

    def test_on_master_passes_through(self, repo: Path):
        _git(repo, "branch", "-M", "master")
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        entries = _read_jsonl(hook_log)
        assert any("master" in e.get("reason", "").lower() for e in entries)

    def test_detached_head_passes_through(self, repo: Path):
        sha = _git(repo, "rev-parse", "HEAD").strip()
        _git(repo, "checkout", "-q", "--detach", sha)
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        entries = _read_jsonl(hook_log)
        assert any(e.get("status") == "skipped" for e in entries)


# ---------------------------------------------------------------------------
# TestGitUnavailable — non-repo cwd → advisory skip (not silent)
# ---------------------------------------------------------------------------


class TestGitUnavailable:
    def test_not_a_git_repo_passes_through_with_advisory(self, tmp_path: Path):
        (tmp_path / ".claude" / "logs").mkdir(parents=True)
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=tmp_path)
        assert result.returncode == 0
        hook_log = tmp_path / ".claude" / "logs" / "pre-pr-gate.jsonl"
        assert hook_log.exists()
        entries = _read_jsonl(hook_log)
        assert any(e.get("status") == "skipped" for e in entries)
        # no phase-gate entry for skips
        assert not (tmp_path / ".claude" / "logs" / "phase-gates.jsonl").exists()


# ---------------------------------------------------------------------------
# TestMergeBaseUnresolved — base can't be computed → advisory skip
# ---------------------------------------------------------------------------


class TestMergeBaseUnresolved:
    def test_no_main_branch_passes_through_with_advisory(self, repo: Path):
        checkout(repo, "feat/x")
        _git(repo, "branch", "-D", "main")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        entries = _read_jsonl(hook_log)
        assert any(
            e.get("status") == "skipped"
            and "merge-base" in e.get("reason", "").lower()
            for e in entries
        )


# ---------------------------------------------------------------------------
# TestDiffUnavailable — merge-base OK pero git diff falla → skip (no empty-PR)
# ---------------------------------------------------------------------------


@needs_hook
class TestDiffUnavailable:
    def _run(
        self,
        monkeypatch: pytest.MonkeyPatch,
        repo: Path,
        stdin_text: str,
    ) -> int:
        monkeypatch.chdir(repo)
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
        return ppg.main()

    def test_diff_files_returns_none_when_git_fails(self, monkeypatch):
        monkeypatch.setattr(ppg, "_run_git", lambda *a, **kw: None)
        assert ppg.diff_files(Path("/tmp"), "abc123") is None

    def test_diff_files_returns_empty_list_when_git_empty(self, monkeypatch):
        monkeypatch.setattr(ppg, "_run_git", lambda *a, **kw: "")
        assert ppg.diff_files(Path("/tmp"), "abc123") == []

    def test_diff_unavailable_skips_not_empty_pr(self, monkeypatch, repo):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        monkeypatch.setattr(ppg, "diff_files", lambda *a, **kw: None)
        payload = json.dumps(make_bash("gh pr create"))
        rc = self._run(monkeypatch, repo, payload)
        assert rc == 0, "git-diff failure must skip, not deny as empty PR"

    def test_diff_unavailable_log_reason_mentions_diff(
        self, monkeypatch, repo
    ):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        monkeypatch.setattr(ppg, "diff_files", lambda *a, **kw: None)
        payload = json.dumps(make_bash("gh pr create"))
        self._run(monkeypatch, repo, payload)
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        entries = _read_jsonl(hook_log)
        skipped = [e for e in entries if e.get("status") == "skipped"]
        assert any("diff" in e.get("reason", "").lower() for e in skipped)
        # must NOT log an "empty PR" decision (would be a false-deny)
        assert not any(
            "empty pr" in e.get("reason", "").lower()
            for e in entries
            if e.get("decision")
        )

    def test_diff_unavailable_writes_no_phase_gate_entry(
        self, monkeypatch, repo
    ):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        monkeypatch.setattr(ppg, "diff_files", lambda *a, **kw: None)
        payload = json.dumps(make_bash("gh pr create"))
        self._run(monkeypatch, repo, payload)
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        # skip path is hook-log-only (replica de merge-base skip)
        assert not phase_log.exists() or _read_jsonl(phase_log) == []


# ---------------------------------------------------------------------------
# TestEmptyDiff — diff vacío vs merge-base
# ---------------------------------------------------------------------------


class TestEmptyDiff:
    def test_empty_diff_denies_with_empty_pr_reason(self, repo: Path):
        checkout(repo, "feat/x")
        # no commits on feat/x; HEAD == main tip → diff empty
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        # must cite empty PR, NOT mislead with docs-sync
        assert "empty PR" in reason or "no changes" in reason.lower()
        assert "docs-sync" not in reason.lower()
        assert "ROADMAP.md" not in reason
        assert "HANDOFF.md" not in reason

    def test_empty_diff_reason_mentions_base_sha(self, repo: Path):
        checkout(repo, "feat/x")
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "ase" in reason  # "Base:" or "base"


# ---------------------------------------------------------------------------
# TestDocsSyncBaseline — ROADMAP + HANDOFF required always
# ---------------------------------------------------------------------------


class TestDocsSyncBaseline:
    def test_missing_roadmap_denies(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"src/foo.ts": "x\n", "HANDOFF.md": "x\n"})
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "ROADMAP.md" in reason

    def test_missing_handoff_denies(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"src/foo.ts": "x\n", "ROADMAP.md": "x\n"})
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "HANDOFF.md" in reason

    def test_missing_both_baseline_denies_listing_both(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"src/foo.ts": "x\n"})
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "ROADMAP.md" in reason
        assert "HANDOFF.md" in reason

    def test_baseline_present_neutral_path_allows(self, repo: Path):
        """Only ROADMAP+HANDOFF touched (no conditional paths) → allow."""
        checkout(repo, "feat/x")
        commit(repo, "docs", **{"ROADMAP.md": "x\n", "HANDOFF.md": "x\n"})
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# TestDocsSyncConditional — path-triggered doc requirements
# ---------------------------------------------------------------------------


class TestDocsSyncConditional:
    def test_generator_touched_requires_architecture(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "generator/lib/foo.ts": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "docs/ARCHITECTURE.md" in reason
        assert "generator/lib/foo.ts" in reason

    def test_hooks_touched_requires_architecture(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "hooks/foo.py": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "docs/ARCHITECTURE.md" in reason
        assert "hooks/foo.py" in reason

    def test_skills_touched_requires_skills_map(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "skills/foo/SKILL.md": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert ".claude/rules/skills-map.md" in reason

    def test_patterns_touched_requires_architecture(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            ".claude/patterns/bar.md": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "docs/ARCHITECTURE.md" in reason

    def test_multiple_conditionals_both_listed(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "hooks/foo.py": "x\n",
            "skills/bar/SKILL.md": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "docs/ARCHITECTURE.md" in reason
        assert ".claude/rules/skills-map.md" in reason

    def test_generator_plus_patterns_dedupes_architecture(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "generator/lib/foo.ts": "x\n",
            ".claude/patterns/bar.md": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        # ARCHITECTURE.md must appear exactly once as a missing-doc entry
        # (not duplicated because both triggers point to the same required doc)
        assert reason.count("docs/ARCHITECTURE.md — required by") == 1

    def test_conditional_satisfied_allows(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "hooks/foo.py": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
            "docs/ARCHITECTURE.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0

    def test_multiple_conditionals_all_satisfied_allows(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "hooks/foo.py": "x\n",
            "skills/bar/SKILL.md": "x\n",
            ".claude/patterns/baz.md": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
            "docs/ARCHITECTURE.md": "x\n",
            ".claude/rules/skills-map.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0

    def test_non_conditional_path_does_not_trigger(self, repo: Path):
        """tests/ touched does NOT require ARCHITECTURE.md (out of conditional set)."""
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "hooks/tests/test_foo.py": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# TestDecisionReason — content assertions
# ---------------------------------------------------------------------------


class TestDecisionReason:
    def test_docs_deny_reason_references_docs_sync(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "docs-sync" in reason.lower()
        assert "CLAUDE.md" in reason

    def test_triggering_paths_listed_for_conditional(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "generator/lib/a.ts": "x\n",
            "generator/lib/b.ts": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "generator/lib/a.ts" in reason or "generator/lib/b.ts" in reason

    def test_triggering_paths_capped_at_three_with_more_indicator(self, repo: Path):
        checkout(repo, "feat/x")
        files = {f"generator/lib/f{i}.ts": "x\n" for i in range(6)}
        files["ROADMAP.md"] = "x\n"
        files["HANDOFF.md"] = "x\n"
        commit(repo, "impl", **files)
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        reason = parse_stdout(result)["hookSpecificOutput"]["decisionReason"]
        assert "more" in reason.lower()


# ---------------------------------------------------------------------------
# TestAdvisoryLogs — deferred scaffold (skills / ci / invariants)
# ---------------------------------------------------------------------------


class TestAdvisoryLogs:
    ADVISORY_CHECKS = {"skills_required", "ci_dry_run_required", "invariants_check"}

    def test_deny_emits_three_deferred_entries(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        entries = _read_jsonl(hook_log)
        deferred = [e for e in entries if e.get("status") == "deferred"]
        checks = {e.get("check") for e in deferred}
        assert checks == self.ADVISORY_CHECKS

    def test_allow_emits_three_deferred_entries(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "hooks/foo.py": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
            "docs/ARCHITECTURE.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        entries = _read_jsonl(hook_log)
        deferred = [e for e in entries if e.get("status") == "deferred"]
        assert {e.get("check") for e in deferred} == self.ADVISORY_CHECKS

    def test_empty_diff_also_emits_three_deferred_entries(self, repo: Path):
        checkout(repo, "feat/x")
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        entries = _read_jsonl(hook_log)
        deferred = [e for e in entries if e.get("status") == "deferred"]
        assert {e.get("check") for e in deferred} == self.ADVISORY_CHECKS

    def test_skip_does_not_emit_deferred_entries(self, repo: Path):
        """On main → advisory skip log only, no deferred checks emitted."""
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        entries = _read_jsonl(hook_log)
        deferred = [e for e in entries if e.get("status") == "deferred"]
        assert deferred == []


# ---------------------------------------------------------------------------
# TestLogging — double-log on decisions, single advisory on skip, silent on no-match
# ---------------------------------------------------------------------------


class TestLogging:
    def test_deny_writes_both_logs(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        assert hook_log.exists()
        assert phase_log.exists()
        hook_entries = _read_jsonl(hook_log)
        assert any(
            e.get("hook") == "pre-pr-gate" and e.get("decision") == "deny"
            for e in hook_entries
        )
        phase_entries = _read_jsonl(phase_log)
        assert phase_entries[-1]["event"] == "pre_pr"
        assert phase_entries[-1]["decision"] == "deny"
        assert "ts" in phase_entries[-1]

    def test_allow_writes_both_logs(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "hooks/foo.py": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
            "docs/ARCHITECTURE.md": "x\n",
        })
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        assert hook_log.exists()
        assert phase_log.exists()
        hook_entries = _read_jsonl(hook_log)
        assert any(e.get("decision") == "allow" for e in hook_entries)
        phase_entries = _read_jsonl(phase_log)
        assert phase_entries[-1]["event"] == "pre_pr"
        assert phase_entries[-1]["decision"] == "allow"

    def test_empty_diff_writes_both_logs(self, repo: Path):
        checkout(repo, "feat/x")
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        assert hook_log.exists()
        assert phase_log.exists()

    def test_skip_writes_only_hook_log_no_phase(self, repo: Path):
        """main-branch skip → hook log gets advisory, phase-gates untouched."""
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        assert hook_log.exists()
        assert not phase_log.exists()

    def test_no_match_does_not_log(self, repo: Path):
        """git status / gh pr list → silent pass-through, zero log."""
        result = run_hook(make_bash("git status"), cwd=repo)
        assert result.returncode == 0
        assert not (repo / ".claude" / "logs" / "pre-pr-gate.jsonl").exists()
        assert not (repo / ".claude" / "logs" / "phase-gates.jsonl").exists()

    def test_non_bash_does_not_log(self, repo: Path):
        result = run_hook(load_fixture("non_bash.json"), cwd=repo)
        assert result.returncode == 0
        assert not (repo / ".claude" / "logs" / "pre-pr-gate.jsonl").exists()

    def test_gh_pr_list_does_not_log(self, repo: Path):
        result = run_hook(load_fixture("gh_pr_list.json"), cwd=repo)
        assert result.returncode == 0
        assert not (repo / ".claude" / "logs" / "pre-pr-gate.jsonl").exists()

    def test_log_entry_shape_on_deny(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        result = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert result.returncode == 2
        hook_entries = _read_jsonl(
            repo / ".claude" / "logs" / "pre-pr-gate.jsonl"
        )
        decision_entry = next(e for e in hook_entries if e.get("decision") == "deny")
        assert decision_entry["hook"] == "pre-pr-gate"
        assert "ts" in decision_entry
        assert "reason" in decision_entry


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
        payload = {"tool_name": "Bash", "tool_input": "bogus"}
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 2

    def test_tool_input_null_passes_through(self, repo: Path):
        payload = {"tool_name": "Bash", "tool_input": None}
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_missing_command_passes_through(self, repo: Path):
        payload = {"tool_name": "Bash", "tool_input": {}}
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_command_not_string_passes_through(self, repo: Path):
        payload = {"tool_name": "Bash", "tool_input": {"command": 42}}
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_command_empty_passes_through(self, repo: Path):
        result = run_hook(make_bash(""), cwd=repo)
        assert result.returncode == 0

    def test_command_whitespace_passes_through(self, repo: Path):
        result = run_hook(make_bash("   "), cwd=repo)
        assert result.returncode == 0

    def test_unparsable_shlex_passes_through(self, repo: Path):
        """Unterminated quote → shlex raises ValueError → not gh pr create → pass-through."""
        result = run_hook(make_bash('gh pr create --title "unterminated'), cwd=repo)
        assert result.returncode == 0

    def test_idempotent_on_deny(self, repo: Path):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        r1 = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        r2 = run_hook(load_fixture("gh_pr_create.json"), cwd=repo)
        assert r1.returncode == r2.returncode == 2


# ---------------------------------------------------------------------------
# TestIsGhPrCreateUnit — matcher classifier unit tests (in-process)
# ---------------------------------------------------------------------------


@needs_hook
class TestIsGhPrCreateUnit:
    def test_plain(self):
        assert ppg.is_gh_pr_create("gh pr create") is True

    def test_with_title(self):
        assert ppg.is_gh_pr_create('gh pr create --title "X"') is True

    def test_with_draft(self):
        assert ppg.is_gh_pr_create("gh pr create --draft") is True

    def test_with_body(self):
        assert ppg.is_gh_pr_create('gh pr create --body "desc"') is True

    def test_with_base(self):
        assert ppg.is_gh_pr_create("gh pr create --base main") is True

    def test_list_excluded(self):
        assert ppg.is_gh_pr_create("gh pr list") is False

    def test_view_excluded(self):
        assert ppg.is_gh_pr_create("gh pr view 123") is False

    def test_edit_excluded(self):
        assert ppg.is_gh_pr_create("gh pr edit 123 --body x") is False

    def test_issue_create_excluded(self):
        assert ppg.is_gh_pr_create("gh issue create") is False

    def test_git_push_excluded(self):
        assert ppg.is_gh_pr_create("git push origin HEAD") is False

    def test_git_status_excluded(self):
        assert ppg.is_gh_pr_create("git status") is False

    def test_empty_excluded(self):
        assert ppg.is_gh_pr_create("") is False

    def test_whitespace_excluded(self):
        assert ppg.is_gh_pr_create("   ") is False

    def test_unparsable_shlex_excluded(self):
        assert ppg.is_gh_pr_create('gh pr create --title "unterminated') is False


# ---------------------------------------------------------------------------
# TestCheckDocsSyncUnit — docs-sync classifier unit tests
# ---------------------------------------------------------------------------


def _test_rules():
    """Construct the rules shape the unit tests use — mirrors POLICY_YAML_FOR_TESTS."""
    sys.path.insert(0, str(REPO_ROOT / "hooks"))
    from _lib.policy import ConditionalRule, DocsSyncRules
    return DocsSyncRules(
        baseline=("ROADMAP.md", "HANDOFF.md"),
        conditional=(
            ConditionalRule(("generator/**",), ("docs/ARCHITECTURE.md",), ()),
            ConditionalRule(("hooks/**",), ("docs/ARCHITECTURE.md",), ("hooks/tests/**",)),
            ConditionalRule(("skills/**",), (".claude/rules/skills-map.md",), ()),
            ConditionalRule((".claude/patterns/**",), ("docs/ARCHITECTURE.md",), ()),
        ),
    )


@needs_hook
class TestCheckDocsSyncUnit:
    def test_baseline_present_no_missing(self):
        missing, _ = ppg.check_docs_sync(
            ["ROADMAP.md", "HANDOFF.md", "docs/X.md"], _test_rules(),
        )
        assert missing == []

    def test_missing_roadmap(self):
        missing, _ = ppg.check_docs_sync(["HANDOFF.md", "src/foo.py"], _test_rules())
        assert "ROADMAP.md" in missing

    def test_missing_handoff(self):
        missing, _ = ppg.check_docs_sync(["ROADMAP.md", "src/foo.py"], _test_rules())
        assert "HANDOFF.md" in missing

    def test_missing_both_baseline(self):
        missing, _ = ppg.check_docs_sync(["src/foo.py"], _test_rules())
        assert "ROADMAP.md" in missing
        assert "HANDOFF.md" in missing

    def test_generator_triggers_architecture(self):
        missing, triggers = ppg.check_docs_sync(
            ["generator/lib/x.ts", "ROADMAP.md", "HANDOFF.md"], _test_rules(),
        )
        assert "docs/ARCHITECTURE.md" in missing
        assert "generator/lib/x.ts" in triggers["docs/ARCHITECTURE.md"]

    def test_hooks_triggers_architecture(self):
        missing, triggers = ppg.check_docs_sync(
            ["hooks/foo.py", "ROADMAP.md", "HANDOFF.md"], _test_rules(),
        )
        assert "docs/ARCHITECTURE.md" in missing
        assert "hooks/foo.py" in triggers["docs/ARCHITECTURE.md"]

    def test_skills_triggers_skills_map(self):
        missing, triggers = ppg.check_docs_sync(
            ["skills/foo/SKILL.md", "ROADMAP.md", "HANDOFF.md"], _test_rules(),
        )
        assert ".claude/rules/skills-map.md" in missing

    def test_patterns_triggers_architecture(self):
        missing, _ = ppg.check_docs_sync(
            [".claude/patterns/bar.md", "ROADMAP.md", "HANDOFF.md"], _test_rules(),
        )
        assert "docs/ARCHITECTURE.md" in missing

    def test_generator_and_patterns_dedupe_architecture(self):
        missing, _ = ppg.check_docs_sync(
            ["generator/lib/x.ts", ".claude/patterns/p.md",
             "ROADMAP.md", "HANDOFF.md"],
            _test_rules(),
        )
        assert missing.count("docs/ARCHITECTURE.md") == 1

    def test_triggers_cap_at_three(self):
        files = [f"generator/lib/f{i}.ts" for i in range(10)] + [
            "ROADMAP.md", "HANDOFF.md",
        ]
        _missing, triggers = ppg.check_docs_sync(files, _test_rules())
        assert len(triggers["docs/ARCHITECTURE.md"]) == 3

    def test_architecture_present_not_missing(self):
        missing, _ = ppg.check_docs_sync(
            ["generator/lib/x.ts",
             "ROADMAP.md", "HANDOFF.md", "docs/ARCHITECTURE.md"],
            _test_rules(),
        )
        assert "docs/ARCHITECTURE.md" not in missing

    def test_skills_map_present_not_missing(self):
        missing, _ = ppg.check_docs_sync(
            ["skills/foo/SKILL.md",
             "ROADMAP.md", "HANDOFF.md", ".claude/rules/skills-map.md"],
            _test_rules(),
        )
        assert ".claude/rules/skills-map.md" not in missing

    def test_tests_alone_do_not_trigger_conditional(self):
        """hooks/tests/** is a valid touched path but should NOT require ARCHITECTURE."""
        missing, _ = ppg.check_docs_sync(
            ["hooks/tests/test_foo.py", "ROADMAP.md", "HANDOFF.md"], _test_rules(),
        )
        assert "docs/ARCHITECTURE.md" not in missing


# ---------------------------------------------------------------------------
# TestMainInProcess — paths subprocess coverage tool cannot reach
# ---------------------------------------------------------------------------


@needs_hook
class TestMainInProcess:
    def _run(
        self,
        monkeypatch: pytest.MonkeyPatch,
        repo: Path,
        stdin_text: str,
    ) -> int:
        monkeypatch.chdir(repo)
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
        return ppg.main()

    def test_malformed_json_returns_2(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, "not json") == 2

    def test_non_dict_payload_returns_2(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, "[1,2,3]") == 2

    def test_non_bash_returns_0(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, '{"tool_name": "Edit"}') == 0

    def test_bash_null_tool_input_returns_0(self, monkeypatch, repo):
        payload = '{"tool_name": "Bash", "tool_input": null}'
        assert self._run(monkeypatch, repo, payload) == 0

    def test_bash_list_tool_input_returns_2(self, monkeypatch, repo):
        payload = '{"tool_name": "Bash", "tool_input": [1,2]}'
        assert self._run(monkeypatch, repo, payload) == 2

    def test_bash_missing_command_returns_0(self, monkeypatch, repo):
        payload = '{"tool_name": "Bash", "tool_input": {}}'
        assert self._run(monkeypatch, repo, payload) == 0

    def test_bash_non_gh_pr_returns_0(self, monkeypatch, repo):
        payload = json.dumps(make_bash("git status"))
        assert self._run(monkeypatch, repo, payload) == 0

    def test_bash_gh_pr_create_on_main_returns_0(self, monkeypatch, repo):
        payload = json.dumps(make_bash("gh pr create"))
        assert self._run(monkeypatch, repo, payload) == 0

    def test_bash_gh_pr_create_empty_diff_returns_2(self, monkeypatch, repo):
        checkout(repo, "feat/x")
        payload = json.dumps(make_bash("gh pr create"))
        assert self._run(monkeypatch, repo, payload) == 2

    def test_bash_gh_pr_create_docs_missing_returns_2(self, monkeypatch, repo):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        payload = json.dumps(make_bash("gh pr create"))
        assert self._run(monkeypatch, repo, payload) == 2

    def test_bash_gh_pr_create_docs_satisfied_returns_0(self, monkeypatch, repo):
        checkout(repo, "feat/x")
        commit(repo, "impl", **{
            "hooks/foo.py": "x\n",
            "ROADMAP.md": "x\n",
            "HANDOFF.md": "x\n",
            "docs/ARCHITECTURE.md": "x\n",
        })
        payload = json.dumps(make_bash("gh pr create"))
        assert self._run(monkeypatch, repo, payload) == 0

    def test_bash_gh_pr_create_unresolved_base_returns_0(self, monkeypatch, repo):
        """No main branch → merge-base unresolved → advisory skip."""
        checkout(repo, "feat/x")
        _git(repo, "branch", "-D", "main")
        commit(repo, "impl", **{"hooks/foo.py": "x\n"})
        payload = json.dumps(make_bash("gh pr create"))
        assert self._run(monkeypatch, repo, payload) == 0

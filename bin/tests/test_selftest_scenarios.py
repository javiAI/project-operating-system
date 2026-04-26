"""F3 scenario contract — each scenario asserts the orchestrator emits
`[ok] D{N} {name}` on its line.

Module-scoped fixture runs `pos-selftest.sh` once and shares stdout across
scenario tests. RED until `bin/_selftest.py` registers the scenario; GREEN
once the scenario passes against the synthetic project.
"""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SELFTEST_SH = REPO_ROOT / "bin" / "pos-selftest.sh"


@pytest.fixture(scope="module")
def selftest_run():
    assert SELFTEST_SH.is_file(), f"missing: {SELFTEST_SH}"
    return subprocess.run(
        [str(SELFTEST_SH)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )


class TestScenarios:
    def test_d1_pre_branch_gate(self, selftest_run):
        assert "[ok] D1 pre-branch-gate" in selftest_run.stdout, (
            f"D1 scenario did not pass\n"
            f"--- exit ---\n{selftest_run.returncode}\n"
            f"--- stdout ---\n{selftest_run.stdout}\n"
            f"--- stderr ---\n{selftest_run.stderr}"
        )

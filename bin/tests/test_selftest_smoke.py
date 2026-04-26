"""F3 RED smoke — locks down bin/pos-selftest.sh contract.

Fails until:
- bin/pos-selftest.sh exists and is executable
- bin/_selftest.py exists (Python orchestrator)
- The shell wrapper delegates to python3 _selftest.py
- Running the wrapper exits 0 against current repo state
"""

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SELFTEST_SH = REPO_ROOT / "bin" / "pos-selftest.sh"
SELFTEST_PY = REPO_ROOT / "bin" / "_selftest.py"


class TestSelftestScriptShape:
    def test_wrapper_exists(self):
        assert SELFTEST_SH.is_file(), f"missing: {SELFTEST_SH}"

    def test_wrapper_is_executable(self):
        assert SELFTEST_SH.is_file(), f"missing: {SELFTEST_SH}"
        assert os.access(SELFTEST_SH, os.X_OK), f"not executable: {SELFTEST_SH}"

    def test_orchestrator_exists(self):
        assert SELFTEST_PY.is_file(), f"missing: {SELFTEST_PY}"

    def test_wrapper_delegates_to_python_orchestrator(self):
        assert SELFTEST_SH.is_file(), f"missing: {SELFTEST_SH}"
        body = SELFTEST_SH.read_text()
        assert "python3" in body, "wrapper should invoke python3"
        assert "_selftest.py" in body, "wrapper should reference _selftest.py"
        assert "set -euo pipefail" in body, "wrapper should use strict bash"


class TestSelftestExecution:
    def test_wrapper_exits_zero(self):
        assert SELFTEST_SH.is_file(), f"missing: {SELFTEST_SH}"
        result = subprocess.run(
            [str(SELFTEST_SH)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert result.returncode == 0, (
            f"selftest exited {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

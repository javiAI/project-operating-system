#!/usr/bin/env python3
"""pos-selftest orchestrator.

End-to-end selftest of the pos plugin: generates a synthetic project via
`npx tsx generator/run.ts --profile questionnaire/profiles/cli-tool.yaml`
and exercises the functional-critical gates against it.

Scope (ratified in F3 Fase -1):
- D1 pre-branch-gate (deny without marker)
- D3 pre-write-guard (deny write without test pair)
- D4 pre-pr-gate (deny PR with docs-sync missing)
- D5 post-action (confirmed merge emits /pos:compound suggestion)
- D6 stop-policy-check (allow/deny skill allowlist)

Out of scope: D2 session-start + D6 pre-compact (informative-only),
Claude Code runtime invocations, real skill/agent dispatch.

Stdlib only. No third-party deps.
"""

from __future__ import annotations

import sys


def main() -> int:
    # Scenarios registered in subsequent commits.
    print("pos-selftest: smoke (no scenarios registered yet)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

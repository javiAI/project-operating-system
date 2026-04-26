#!/usr/bin/env bash
set -euo pipefail

# pos-selftest — end-to-end smoke for the pos plugin gates.
# Thin bash wrapper. Orchestration lives in bin/_selftest.py (stdlib only,
# no Claude Code runtime).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/_selftest.py" "$@"

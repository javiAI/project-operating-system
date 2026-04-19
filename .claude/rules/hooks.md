---
name: hooks
description: Reglas cuando editas hooks Python del plugin pos
paths:
  - "hooks/**"
  - ".claude/hooks/**"
---

# Reglas — Hooks Python

## Runtime

- Python 3.10+. Usa type hints (`list`, `dict` nativo, no `List`/`Dict`).
- Cero dependencias fuera de la stdlib salvo justificación explícita en kickoff de rama.
- Shebang `#!/usr/bin/env python3`.
- `chmod +x` obligatorio (hook de commit lo valida).

## Interfaz de hooks Claude Code

- Lee JSON desde stdin; escribe JSON a stdout.
- Campos output standard: `hookSpecificOutput.hookEventName`, `additionalContext`, `permissionDecision`, `decisionReason`.
- Exit code 0 = éxito; exit code 2 = blocking error (Claude Code lo interpreta como `deny`).
- Timeout por defecto: 5000ms (configurable en `settings.local.json`).

## Estructura

```python
#!/usr/bin/env python3
"""Hook <nombre>: <one-liner>."""
import json
import sys
from pathlib import Path

def main() -> int:
    payload = json.load(sys.stdin)
    # ... lógica ...
    result = {"hookSpecificOutput": {"hookEventName": "<event>", ...}}
    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Tests

- `pytest`. Test file pair obligatorio (`hooks/tests/test_<nombre>.py`).
- Usa `subprocess.run([hook_path], input=json.dumps(payload), capture_output=True, text=True, timeout=5)`.
- Fixture `hooks/tests/fixtures/payloads/` con payloads reales capturados.
- Cobertura de: happy path + cada branch de denial + timeout simulado.

## Reglas duras

1. **Nunca** leer `.env`, `~/.ssh/`, `~/.aws/` ni variables con `TOKEN`/`KEY`/`SECRET`/`PASSWORD` sin justificarlo en frontmatter del hook.
2. **Nunca** hacer network calls (`urllib.request`, `socket`, `http.client`) sin declararlo en frontmatter `# network: <host>`.
3. **Nunca** `subprocess` sin `shell=False` + args como lista.
4. **Logs** a `.claude/logs/<hook-name>.jsonl` (append-only, JSONL). No a stdout si no es protocolo.
5. **Idempotencia**: si el hook corre 2 veces con el mismo input, comportamiento igual.

## Auditoría

Cada hook nuevo pasa por `/pos:audit-plugin` antes de entrar en `policy.yaml`. El auditor valida las reglas duras + scope declarado.

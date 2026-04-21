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
- Política safe-fail sobre payload malformado — **dos variantes según el evento**:
  - **Blocker** (`PreToolUse`, `PreCompact`, `Stop`): stdin vacío, JSON inválido, top-level no-dict o campos con tipo imposible de interpretar → `deny` explícito (exit 2 + `decisionReason` que explica el error), nunca pass-through. Un hook que no puede validar su entrada no debe dejarla pasar. Referencia: `pre-branch-gate.py` (D1).
  - **Informative** (`SessionStart`, `UserPromptSubmit` si llegara): nunca emite `permissionDecision`, nunca exit 2. Payload malformado o errores de subprocess/git degradan a `additionalContext` mínimo (p.ej. `(error reading payload: <msg>)`) + log de error; exit 0 siempre. Bloquear un evento informativo dejaría al usuario sin contexto sin ganancia de enforcement. Excepción canónica, no aplicable a blocker hooks. Referencia: `session-start.py` (D2).

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

## Primer hook entregado — `hooks/pre-branch-gate.py` (Rama D1)

Referencia del patrón **blocker** (PreToolUse):

- Pass-through silencioso: cero stdout salvo cuando el hook tiene algo que decir (deny). Nunca loggea en pass-through (evita ruido en `.claude/logs/`).
- Detección del contexto Bash con `shlex.split` (no regex). Maneja global options git pre-subcommand (`git -c k=v ...`, `--git-dir=X`, `-C /path`).
- `decisionReason` constructivo: ruta exacta del recurso esperado + comando sugerido (`touch <path>`) + referencia textual a docs (`MASTER_PLAN.md`). Sin parseo de docs ni inferencia.
- Double log: `.claude/logs/<hook-name>.jsonl` (shape propio) + `.claude/logs/phase-gates.jsonl` (evento canónico del lifecycle). Las ramas D3..D6 siguen este shape.
- Tests pytest: 23 subprocess (integración end-to-end) + 32 in-process (coverage visible, carga del módulo con `importlib.util.spec_from_file_location` por guión en el nombre). `.venv` local + `requirements-dev.txt` mínimo.

## Segundo hook entregado — `hooks/session-start.py` (Rama D2)

Referencia del patrón **informative** (SessionStart) — primera aplicación de la excepción safe-fail graceful:

- Emite `hookSpecificOutput.additionalContext` con snapshot ≤10 líneas (Branch / Phase / Last merge / Warnings). Sin `permissionDecision`, sin exit 2 bajo ningún camino.
- Fase derivada vía regex `^(feat|fix|chore|refactor)[/_]([a-z])(\d+)-` sobre nombre de rama; fallback a `.claude/logs/phase-gates.jsonl` en `main`/`master`; `unknown` si ninguna fuente resuelve. No parsea `ROADMAP.md`/`MASTER_PLAN.md` (evita acoplamiento + coste).
- Subprocess git robusto: `shell=False`, `cwd=` explícito, `timeout=2`, `check=False`, captura `FileNotFoundError` + `SubprocessError`; `None` en error — el caller decide degradación. Ningún camino sube excepción.
- Warnings estructurales (no conversacionales): marker ausente + docs-sync pendiente. Suprimidos en `main`/`master` y cuando git no está disponible.
- Double log: `session-start.jsonl` + `phase-gates.jsonl` (evento `session_start`). Mismo shape que D1.
- Tests pytest: 30 subprocess + 36 in-process (66 total). `TestMainInProcess` específicamente para cubrir los caminos git (pytest-cov no mide subprocess). 95% coverage sobre `session-start.py`.

## Helpers compartidos — `hooks/_lib/` (extraído en D2)

Segunda repetición de CLAUDE.md regla #7 cumplida (D1 + D2 = 2 hooks reusando los mismos patrones). Contenido mínimo:

- `_lib/slug.py::sanitize_slug` (`/` → `_`).
- `_lib/jsonl.py::append_jsonl` + `read_jsonl` (append-only + reader tolerante a líneas inválidas).
- `_lib/time.py::now_iso` (UTC ISO-8601).
- `_lib/__init__.py` vacío (package marker).

**Cómo consumir desde un hook con nombre hyphenated** (no importable como módulo Python):

```python
sys.path.insert(0, str(Path(__file__).parent))
from _lib.slug import sanitize_slug  # noqa: E402
from _lib.jsonl import append_jsonl, read_jsonl  # noqa: E402
from _lib.time import now_iso  # noqa: E402
```

Las ramas D3..D6 **deben reusar** estos helpers en lugar de redefinir. Añadir a `_lib/` sólo cuando ≥2 hooks usen el nuevo helper (regla #7 sigue aplicando incrementalmente). No añadir tests en `hooks/tests/test_lib/` salvo que `_lib/` crezca a lógica no trivial — se testea via los hooks que lo consumen.

Ver [ROADMAP.md § Progreso Fase D](../../ROADMAP.md) para el detalle de entregables y ajustes.

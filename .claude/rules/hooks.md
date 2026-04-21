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
  - **Informative** (`SessionStart`, `UserPromptSubmit` si llegara): nunca emite `permissionDecision`, nunca exit 2. Payload malformado → `additionalContext` mínimo (p.ej. `(error reading payload: <msg>)`) + entrada en `_log_error` (solo `session-start.jsonl`). Errores de subprocess/git → `additionalContext` mínimo + `_log_snapshot` sigue emitiendo la entrada happy-path (campos que dependen de git caen a `None`/`"unknown"`); lo que se omite es el *error log* (helpers tipo `_git` devuelven `None` sin invocar `_log_error`). Fallos del propio logging (disk full, RO fs) se tragan vía wrapper tipo `_safe_append`. Exit 0 siempre. Bloquear un evento informativo dejaría al usuario sin contexto sin ganancia de enforcement. Excepción canónica, no aplicable a blocker hooks. Referencia: `session-start.py` (D2).

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
- `_lib/jsonl.py::append_jsonl` (append-only JSONL).
- `_lib/time.py::now_iso` (UTC ISO-8601).
- `_lib/__init__.py` vacío (package marker).

**Cómo consumir desde un hook con nombre hyphenated** (no importable como módulo Python):

```python
sys.path.insert(0, str(Path(__file__).parent))
from _lib.slug import sanitize_slug  # noqa: E402
from _lib.jsonl import append_jsonl  # noqa: E402
from _lib.time import now_iso  # noqa: E402
```

Las ramas D3..D6 **deben reusar** estos helpers en lugar de redefinir. Añadir a `_lib/` sólo cuando ≥2 hooks usen el nuevo helper (regla #7 sigue aplicando incrementalmente). No añadir tests en `hooks/tests/test_lib/` salvo que `_lib/` crezca a lógica no trivial — se testea via los hooks que lo consumen.

## Tercer hook entregado — `hooks/pre-write-guard.py` (Rama D3)

Segunda aplicación del patrón **blocker** (PreToolUse(Write)) — shape idéntico a D1, regla específica distinta. Enforza CLAUDE.md regla #3 (test antes que implementación) sobre `hooks/**` y `generator/**`.

- Clasifica cada Write por `tool_input.file_path` (normalizado contra `Path.cwd()`; absolutos fuera del repo → pass-through).
- Contrato crystal-clear que la suite fija sin ambigüedad:
  - enforced + archivo inexistente + sin test pair → **deny exit 2** con `decisionReason` construido (ruta esperada + comando `touch` + referencia a CLAUDE.md regla #3 + write bloqueado).
  - enforced + archivo inexistente + con test pair → **allow exit 0** (double log).
  - enforced + archivo ya existente → **allow exit 0** — edit flow (double log; fricción en rewrites queda para D4 `pre-pr-gate`).
  - excluido o fuera de scope → **pass-through silencioso** (cero stdout, cero log).
- Double log: `.claude/logs/pre-write-guard.jsonl` (`{ts, hook, file_path, decision, reason}`) + `.claude/logs/phase-gates.jsonl` (evento `pre_write`, `{ts, event, file_path, decision}`). Pass-throughs NO loguean (replica D1; evita ruido).
- Safe-fail blocker canonical: stdin vacío / JSON inválido / top-level no-dict / `tool_input` no-dict → deny exit 2. `file_path` ausente o no-string → pass-through exit 0 (decisión Fase -1: no es malformación total).
- Reuso `_lib/`: `append_jsonl` + `now_iso`. `sanitize_slug` no aplica (D3 no deriva slugs de file paths). No introduce `read_jsonl`.
- Tests pytest: 83 casos, 95% coverage sobre `pre-write-guard.py`. Suite organizada por clase de contrato (enforced/exclusions/out-of-scope/logging/robustness) + unit tests del clasificador.

### Clasificador — paths (hardcoded hasta D4 mueva la lista a `policy.yaml`)

**Enforced** (requiere test pair cuando se crea archivo nuevo):

| Path pattern | Expected test pair |
|---|---|
| `hooks/<name>.py` (top-level, excluye `_lib/` y `tests/`) | `hooks/tests/test_<name_underscore>.py` (`-` → `_`) |
| `generator/**/<name>.ts` (excluye `*.test.ts`, `__tests__/`, `__fixtures__/`) | `<same-dir>/<name>.test.ts` (co-located) |
| `generator/run.ts` | `generator/run.test.ts` (co-located) — decisión Fase -1 |

**Excluido — Bucket 1: tests / docs / templates / meta**

Pass-through silencioso porque estos archivos **no son implementación a cubrir**. Son input para otros hooks/renderers o documentación:

| Path pattern | Motivo |
|---|---|
| `hooks/tests/**/*.py` | Son los tests; bloquearlos sería circular |
| `**/*.test.ts` | Tests co-located del generador |
| `generator/__tests__/**` | Tests cross-cutting (snapshots) |
| `generator/__fixtures__/**` | Fixtures de tests, no lógica |
| `hooks/README.md` | Documentación del dir |
| `**/*.md` | Docs (ROADMAP, HANDOFF, etc.) — docs-sync lo gobierna D4, no D3 |
| `**/*.yaml`, `**/*.yml` | Schemas, profiles, configs |
| `**/*.json` | `.claude/settings.json`, `package.json`, etc. |
| `**/*.hbs` | Templates Handlebars — no impl directa |
| `**/*.snap` | Snapshots generados por vitest |

**Excluido — Bucket 2: helper internals**

Pass-through silencioso por **decisión explícita del repo (D2)**. Categoría separada a propósito — no se mezcla con Bucket 1 porque la razón es distinta:

| Path pattern | Motivo |
|---|---|
| `hooks/_lib/**/*.py` | Helpers triviales (3-20 líneas cada uno); se testean vía los hooks que los consumen, no aisladamente. Ver HANDOFF.md §10 D2 y nota al final de esta rule. `.claude/rules/hooks.md` L106 ratifica: *"No añadir tests en `hooks/tests/test_lib/` salvo que `_lib/` crezca a lógica no trivial — se testea via los hooks que lo consumen."* |

**Fuera de scope** (también pass-through): cualquier otro path que no caiga en enforced ni en los buckets excluidos — `scripts/**`, paths arbitrarios fuera del repo, etc. No logueados.

Scope recortado (pattern injection + anti-pattern blocking diferidos post-E3a) documentado en [MASTER_PLAN.md § Rama D3](../../MASTER_PLAN.md). Ver también [ROADMAP.md § Progreso Fase D](../../ROADMAP.md).

## Cuarto hook entregado — `hooks/pre-pr-gate.py` (Rama D4)

Tercera aplicación del patrón **blocker** (PreToolUse(Bash)) — shape idéntico a D1, regla específica distinta. Enforza CLAUDE.md regla #2 (docs-sync dentro de la rama) sobre `gh pr create`.

- Matcher con `shlex.split`: activa sólo si `tokens[:3] == ["gh", "pr", "create"]`. Cualquier otro comando Bash → pass-through silencioso.
- Contrato:
  - diff vacío (no commits vs `merge-base HEAD main`) → **deny exit 2** con razón dedicada (`empty PR`) — no intenta check de docs.
  - diff con docs-sync baseline ausente (falta `ROADMAP.md` o `HANDOFF.md`) → **deny exit 2** con lista de docs faltantes + paths que los disparan.
  - diff que toca `generator/`, `hooks/` (excl. `hooks/tests/`), `skills/` o `.claude/patterns/` sin su doc condicional → **deny exit 2** mismo shape de razón.
  - todo docs-sync presente → **allow exit 0** (double log).
  - rama `main`/`master`, `HEAD` detached, git no disponible o `merge-base` sin resolver → **pass-through exit 0** con log `status: skipped` (permite crear el primer PR contra `main` sin historia previa).
- `decisionReason` constructivo: baseline listado con motivo literal (`required baseline (every PR)`); condicionales acompañados de los paths que los dispararon (cap 3 + `... (+N more)`). Sin parseo de docs.
- Double log: `.claude/logs/pre-pr-gate.jsonl` (`{ts, hook, command, decision, reason}` en decisiones; `{ts, hook, command, status: skipped, reason}` en pass-throughs advisory) + `.claude/logs/phase-gates.jsonl` (evento `pre_pr`, sólo en decisiones reales). Pass-throughs non-matcher (comando Bash que no es `gh pr create`) NO loguean (replica D1).
- Advisory scaffold (`skills_required`, `ci_dry_run_required`, `invariants_check`) persistido como entradas `status: deferred` en el log del hook sólo cuando hay decisión real. Shape ya preparado para cuando skills/invariants lleguen en E*/F; no bloquea.
- Reglas hardcoded — mirror literal de `policy.yaml.lifecycle.pre_pr.docs_sync_baseline` / `docs_sync_conditional`. Parse real deferido a rama policy-loader (CLAUDE.md regla #7: dos repeticiones antes de abstraer).
- Safe-fail blocker canonical (D1): stdin no-JSON / top-level no-dict / `tool_input` no-dict → **deny exit 2**. `command` ausente, no-string o vacío → pass-through exit 0 (payload válido pero fuera de scope).
- Reuso `_lib/`: `append_jsonl` + `now_iso`. `sanitize_slug` no aplica. No introduce helpers nuevos a `_lib/`.
- Tests pytest: 96 casos (subprocess end-to-end + in-process via `importlib.util.spec_from_file_location` por guión en el nombre), 93% coverage sobre `pre-pr-gate.py`. Fixture `repo` crea git real + commits para cubrir los caminos de `merge-base`/`diff`.

### Docs-sync reglas (hardcoded en D4, migra a `policy.yaml` en rama policy-loader)

**Baseline** (obligatorio en todo PR):

| Doc          | Motivo                                                   |
|--------------|----------------------------------------------------------|
| `ROADMAP.md` | Estado vivo; toda rama altera al menos la fila de su fase |
| `HANDOFF.md` | Quickref 30s; se reescribe al cerrar la rama             |

**Condicional** (por prefijo de path tocado):

| Prefijo de path      | Doc requerido                  | Excluye         |
|----------------------|--------------------------------|-----------------|
| `generator/`         | `docs/ARCHITECTURE.md`         | —               |
| `hooks/`             | `docs/ARCHITECTURE.md`         | `hooks/tests/`  |
| `skills/`            | `.claude/rules/skills-map.md`  | —               |
| `.claude/patterns/`  | `docs/ARCHITECTURE.md`         | —               |

La primera regla matcheada gana (ciclo de `CONDITIONAL_RULES` con `break`). Si un path no matchea ningún prefijo → no dispara docs-sync extra (baseline sigue aplicando).

Ver también [MASTER_PLAN.md § Rama D4](../../MASTER_PLAN.md), [docs/ARCHITECTURE.md §7](../../docs/ARCHITECTURE.md#capa-1-hooks).

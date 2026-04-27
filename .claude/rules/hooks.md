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
  - diff vacío real (`git diff --name-only <base> HEAD` devuelve `[]`) → **deny exit 2** con razón dedicada (`empty PR`) — no intenta check de docs.
  - diff con docs-sync required ausente (falta `ROADMAP.md` o `HANDOFF.md`) → **deny exit 2** con lista de docs faltantes + paths que los disparan.
  - diff que toca `generator/`, `hooks/` (excl. `hooks/tests/`), `skills/` o `.claude/patterns/` sin su doc condicional → **deny exit 2** mismo shape de razón.
  - todo docs-sync presente → **allow exit 0** (double log).
  - rama `main`/`master`, `HEAD` detached, git no disponible, `merge-base` sin resolver, o `git diff` subprocess falla (`diff_files() is None`, distinto de diff vacío) → **pass-through exit 0** con log `status: skipped` (permite crear el primer PR contra `main` sin historia previa y no bloquea por falsos vacíos).
- `decisionReason` constructivo: los docs required se listan con motivo literal `required baseline (every PR)` (string literal emitido por el hook; el concepto se corresponde con `policy.yaml.lifecycle.pre_pr.docs_sync_required`); condicionales acompañados de los paths que los dispararon (cap 3 + `... (+N more)`). Sin parseo de docs.
- Double log: `.claude/logs/pre-pr-gate.jsonl` (`{ts, hook, command, decision, reason}` en decisiones; `{ts, hook, command, status: skipped, reason}` en pass-throughs advisory) + `.claude/logs/phase-gates.jsonl` (evento `pre_pr`, sólo en decisiones reales). Pass-throughs non-matcher (comando Bash que no es `gh pr create`) NO loguean (replica D1).
- Advisory scaffold (`skills_required`, `ci_dry_run_required`, `invariants_check`) persistido como entradas `status: deferred` en el log del hook sólo cuando hay decisión real. Shape ya preparado para cuando skills/invariants lleguen en E*/F; no bloquea.
- Reglas hardcoded — mirror literal de `policy.yaml.lifecycle.pre_pr.docs_sync_required` / `docs_sync_conditional`. Parse real deferido a rama policy-loader (CLAUDE.md regla #7: dos repeticiones antes de abstraer).
- **Divergencia deliberada `hooks/tests/`**: el hook excluye `hooks/tests/` del trigger condicional `hooks/** → docs/ARCHITECTURE.md`; `policy.yaml` lista `hooks/**` uniforme. No se reconcilia en D4 (la lógica del hook es la correcta: tests no son impl arquitectural). La convergencia hook ↔ policy se resuelve en la rama policy-loader (si el loader representa exclusiones granulares o si la policy se vuelve más específica).
- `diff_files` devuelve `list[str] | None`: `None` = git diff no disponible (skip advisory con `status: "skipped"`), `[]` = diff verdaderamente vacío (deny con `empty PR`). Distinguir evita false-deny cuando `git diff` subprocess falla tras `merge-base` OK.
- Safe-fail blocker canonical (D1): stdin no-JSON / top-level no-dict / `tool_input` no-dict → **deny exit 2**. `command` ausente, no-string o vacío → pass-through exit 0 (payload válido pero fuera de scope).
- Reuso `_lib/`: `append_jsonl` + `now_iso`. `sanitize_slug` no aplica. No introduce helpers nuevos a `_lib/`.
- Tests pytest: 101 casos (subprocess end-to-end + in-process via `importlib.util.spec_from_file_location` por guión en el nombre), ≥94% coverage sobre `pre-pr-gate.py`; suite global `hooks/**`: 322 pasados (D1+D2+D3+D4). Fixture `repo` crea git real + commits para cubrir los caminos de `merge-base`/`diff`; `TestDiffUnavailable` monkeypatches `diff_files` para el caso diff-no-disponible (`None` vs `[]`).

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

La primera regla matcheada gana (ciclo de `CONDITIONAL_RULES` con `break`). Si un path no matchea ningún prefijo → no dispara docs-sync condicional extra (los docs required `ROADMAP.md` + `HANDOFF.md` siguen aplicando en todo PR).

Ver también [MASTER_PLAN.md § Rama D4](../../MASTER_PLAN.md), [docs/ARCHITECTURE.md §7](../../docs/ARCHITECTURE.md#capa-1-hooks).

## Quinto hook entregado — `hooks/post-action.py` (Rama D5)

Primera aplicación del patrón **PostToolUse non-blocking** — tercer patrón canónico de la Capa 1 (tras blocker D1 e informative D2). Shape emparentado con el blocker D1 (shlex + double log + importlib-friendly + reuso `_lib/`), pero **exit 0 siempre** y nunca emite `permissionDecision` ni exit 2.

Enforza trigger advisory de `/pos:compound` (CLAUDE.md § Flujo de rama Fase N+6) sobre merges/pulls locales que tocan paths configurados.

- **Detección jerárquica 2 tiers** — separa intención (comando ejecutado) de resultado (estado local post-acción):
  - **Tier 1** (`shlex.split(command)`, `tokens[0] == "git"`): matcher A `tokens[1] == "merge"` + ningún token en `{--abort, --quit, --continue, --skip}`; matcher C `tokens[1] == "pull"` + ningún token en `{--rebase, -r}`. Otros comandos (`git rebase`, `gh pr merge`, non-git) → early return 0 silencioso.
  - **Tier 2** (`git reflog HEAD -1 --format=%gs`): matcher A confirma prefijo `"merge "`; matcher C confirma prefijo `"pull:" | "pull "` y NO `"pull --rebase"`. Descarta `git merge --abort`, merges `--ff-only` que no pudieron fast-forward (no tocaron HEAD), y pulls que terminaron siendo rebase real sin flag explícito.
- Contrato (exit 0 siempre, 4 status distinguidos + pass-through):
  - Tier 1 miss → pass-through silencioso (cero log, replica D1).
  - Tier 2 no confirma → hook log `status: tier2_unconfirmed`; `phase-gates.jsonl` intacto.
  - Tier 2 OK + `git diff --name-only HEAD@{1} HEAD` falla → hook log `status: diff_unavailable`; `phase-gates.jsonl` intacto.
  - Tier 2 OK + diff OK + trigger miss → hook log `status: confirmed_no_triggers` + `phase-gates.jsonl` evento `post_merge`.
  - Tier 2 OK + diff OK + trigger match → hook log `status: confirmed_triggers_matched` + `phase-gates.jsonl` evento `post_merge` + emite `hookSpecificOutput.additionalContext` (4 líneas, cap 3 paths con `(+N more)`, CTA `Consider running /pos:compound...`).
- **Advisory-only (no dispatch)**. El hook nunca invoca `/pos:compound` — mantiene separación control-plane vs skill-plane. La skill real la entrega E3a; además la skill no existe todavía. Dispatch desde hook es antipatrón canonizado.
- **`gh pr merge` (matcher B) descartado en Fase -1**. Razones: (a) `tool_response.exit_code` no está documentado como contrato estable de Claude Code en PostToolUse(Bash) — sin él no hay forma confiable de distinguir éxito de fallo; (b) el merge ocurre en remoto, no deja reflog local inmediato. Reabrir cuando `gh` deje huella local observable o Claude Code documente `exit_code`.
- **`TRIGGER_GLOBS` / `SKIP_IF_ONLY_GLOBS` / `MIN_FILES_CHANGED` hardcoded** — mirror literal de `policy.yaml.lifecycle.post_merge.skills_conditional[0]`. `fnmatch.fnmatch` sobre paths del diff. Skip si `<MIN_FILES_CHANGED` o si todos los paths caen en `SKIP_IF_ONLY_GLOBS`. **Segunda repetición hardcoded tras D4** → CLAUDE.md regla #7 cumplida dos veces, precondición abierta para la rama policy-loader.
- Subprocess git robusto (reusa patrón D2): `shell=False`, `cwd=Path.cwd()`, `timeout=5`, `check=False`, captura `FileNotFoundError` + `SubprocessError`; `None` en error. Ningún camino sube excepción.
- Safe-fail PostToolUse non-blocking: stdin vacío / JSON inválido / top-level no-dict / `tool_input` no-dict / `tool_name != "Bash"` / `command` ausente o vacío / shlex unparsable → early return 0 silencioso (sin log). Bloquear un PostToolUse es inviable — la acción ya ocurrió; el patrón útil es degradar a no-op.
- Double log: `.claude/logs/post-action.jsonl` (`{ts, hook, command, kind, status, ...}` — `kind ∈ {git_merge, git_pull}`) + `.claude/logs/phase-gates.jsonl` (evento `post_merge`, sólo en los dos status confirmed). Pass-throughs (Tier 1 miss) NO loguean. Los advisory tier2/diff loguean al hook log pero NO al phase-gates — la puerta del lifecycle sólo se cruza con confirmación real.
- Reuso `_lib/`: `append_jsonl` + `now_iso`. Sin nuevos helpers compartidos.
- Tests pytest: 111 casos en `hooks/tests/test_post_action.py` (17 clases — 6 in-process + 11 subprocess integration), 110 passed + 1 skip intencional (`TestIntegrationDiffUnavailable` delega en `TestMainInProcess` vía `pytest.skip` — subprocess no puede cubrir cleanly el camino `diff_files is None`). Fixtures topológicas two-repo (`repo_after_merge`, `repo_after_merge_ff`, `repo_after_pull`): upstream real + local clone + commit divergente + pull/merge real → reflog + diff auténticos. 97% coverage sobre `hooks/post-action.py`; 432 totales en `hooks/**` (D1+D2+D3+D4+D5), sin regresión.

### Simplify pass pre-PR (D5)

Helper privado `_match(path, glob)` inlineado en `match_triggers` — era wrapper trivial sobre `fnmatch.fnmatch` con un solo caller. Reduce 4 líneas sin perder legibilidad; no afecta contrato de tests (el helper era privado).

Ver también [MASTER_PLAN.md § Rama D5](../../MASTER_PLAN.md), [docs/ARCHITECTURE.md §7](../../docs/ARCHITECTURE.md#capa-1-hooks).

## Policy loader — `hooks/_lib/policy.py` (extraído en D5b)

Fuente única de verdad para los hooks frente a `policy.yaml`. Cumple la precondición regla #7 CLAUDE.md abierta por D4 + D5 (dos repeticiones hardcoded de `policy.yaml` dentro del código de los hooks). D3/D4/D5 consumen el loader desde D5b; todo hook futuro debe hacerlo igual.

### Contrato del consumidor

```python
sys.path.insert(0, str(Path(__file__).parent))
from _lib.policy import DocsSyncRules, docs_sync_rules  # noqa: E402
# o: PostMergeTrigger, post_merge_trigger / PreWriteRules, pre_write_rules

def main() -> int:
    # ... validar payload, classify command/tool, etc. ...
    rules = docs_sync_rules(Path.cwd())          # accessor tipado
    if rules is None:                             # failure mode (c.2)
        _log_skip(repo_root, ts, command,
                  status="policy_unavailable",
                  reason="policy.yaml missing or pre_pr section absent")
        return 0                                  # pass-through advisory, NO deny
    # ... consumir rules.baseline / rules.conditional / ...
```

**Regla dura**: ningún hook debe reparsear `policy.yaml` directamente (`yaml.safe_load(...)`) ni redefinir un mirror hardcoded. Si la sección que el hook necesita todavía no tiene accessor, **añade un accessor nuevo** en `_lib/policy.py` (dataclass frozen + función cacheada + test unitario) — no rompas la capa.

### Failure mode canónico — (c.2) pass-through advisory

| Situación                                       | Accessor devuelve | Hook hace                                               |
|-------------------------------------------------|-------------------|---------------------------------------------------------|
| `policy.yaml` no existe                         | `None`            | log `status: policy_unavailable` + pass-through exit 0  |
| `policy.yaml` YAML inválido (parse falla)       | `None`            | idem                                                    |
| `policy.yaml` OK pero sección relevante ausente | `None`            | idem                                                    |
| Happy path                                      | dataclass tipado  | consumir normalmente                                    |

**Prohibido**: `deny` defensivo cuando loader devuelve `None` (brickea PRs ante un typo YAML); fallback hardcoded a defaults (rompe el propósito de tener loader único). Descartadas explícitamente en Fase -1 de D5b.

Esta política es la **tercera variante de safe-fail** en la capa 1 (junto con blocker estricto e informative graceful). Aplica a cualquier hook que lea `policy.yaml`.

### Shape del loader

- `load_policy(repo_root)` — cacheado, clave = path abs **únicamente** (sin mtime/size, sin invalidación implícita por edits al archivo dentro del mismo proceso). `reset_cache()` para test isolation (autouse fixture) o para forzar relectura controlada.
- 6 dataclasses frozen: `ConditionalRule`, `DocsSyncRules`, `PostMergeTrigger`, `EnforcedPattern`, `PreWriteRules`, `PreCompactRules` (la última añadida en D6).
- 5 accessors: `docs_sync_rules(repo_root)` / `post_merge_trigger(repo_root)` / `pre_write_rules(repo_root)` / `pre_compact_rules(repo_root)` / `skills_allowed_list(repo_root)`. Cada uno encapsula un lookup de sección concreto en `policy.yaml` + construcción de la dataclass (o tipo de retorno simple para casos mono-campo). **Contrato tri-estado de `skills_allowed_list` (D6, c.3 scaffold + post-review)**: devuelve `tuple[str, ...] | None | SkillsAllowedInvalid`. `None` = clave absent (deferred — el consumer pasa); `SKILLS_ALLOWED_INVALID` (sentinel exportado) = clave presente pero mal formada, p.ej. escalar / lista con no-strings / dict (misconfigured — el consumer pasa PERO loguea un `status: policy_misconfigured` **observable**, no colapsa con deferred); `()` = lista declarada-vacía (deny-all explícito — el consumer enforza); tupla poblada = enforcement live. Esta distinción permite que el hook Stop separe: (a) "sin allowlist declarada" (prod hoy, pass-through deferred silencioso), (b) "allowlist typo'eada" (pass-through pero observable — un error de policy no apaga enforcement silenciosamente), (c) "allowlist vacía intencional" (bloquea cualquier invocación). Si un hook futuro consume una sección nueva, añadir un accessor siguiendo el mismo patrón — NO reparsear `policy.yaml` dentro del hook.
- `derive_test_pair(rel_path, label)` — derivación procedural keyed por `label` (decisión b.1 Fase -1: strings y globs en YAML, derivación en Python). Dos ramas activas hoy: `hooks_top_level_py` (`hooks/<name>.py` → `hooks/tests/test_<name_underscore>.py`) y `generator_ts` (`generator/**/<name>.ts` → co-located `<dir>/<name>.test.ts`). Añadir rama nueva sólo si ≥2 enforced patterns reales la necesitan.

### Dependencia — `pyyaml==6.0.2`

Primera línea no-stdlib en `hooks/_lib/`. Pin exacto (no `>=6.0,<7`) por contrato: un upgrade semver-minor que cambiara semántica de `yaml.safe_load` rompería todos los hooks silenciosamente; preferimos upgrade explícito. Declarado en `requirements-dev.txt` + justificación permanente en kickoff commit de D5b.

Si un hook futuro necesita otra dep no-stdlib, abrir un commit propio que la justifique en kickoff (mismo patrón).

### Nota fnmatch — middle `/` no es recursivo

`fnmatch.fnmatchcase("generator/run.ts", "generator/**/*.ts")` **NO matchea**. Razón: el middle `/` del `**` es literal en `fnmatch`, no recursivo estilo git. Solución adoptada en `pre_write.enforced_patterns`: dos entries con la misma `label: "generator_ts"` — uno con `match_glob: "generator/*.ts"` (top-level), otro con `match_glob: "generator/**/*.ts"` (subdirs). El loader trata entries como pattern-list; la derivación es label-driven. Aplicar el mismo pattern a cualquier enforced_pattern que quiera cubrir paths top-level + recursivos simultáneamente.

### Tests del loader

- Loader con suite propia: `hooks/tests/test_lib_policy.py` (57 casos — cache behavior, los 3 accessors con happy path + missing section + missing file, `derive_test_pair` por label, invalidación del cache via `reset_cache()`, precedencia del first-match-wins en conditional rules).
- Tests de los 3 hooks consumidores: fixture de repo escribe `policy.yaml` a disco + autouse `_reset_policy_cache` para isolation. Tests unitarios de los consumidores aceptan la dataclass tipada como argumento (`check_docs_sync(files, rules)`, `match_triggers(paths, trigger)`). Constantes hardcoded que eran mirror de `policy.yaml` (`TestIsEnforcedUnit`, `TestExpectedTestPairUnit`, `TestPolicyConstants`) eliminadas por redundantes con el loader test.

### Drift temporal meta-repo ↔ template — cerrado en `refactor/template-policy-d5b-migration`

Tras D5b el `policy.yaml` del meta-repo quedó con el shape nuevo, mientras que `templates/policy.yaml.hbs` siguió emitiendo el shape pre-D5b. El drift se cerró en la rama `refactor/template-policy-d5b-migration` migrando el template a un shape contractual con el loader (`hooks/_lib/policy.py`). Decisiones ratificadas:

- `lifecycle.pre_write.enforced_patterns: []` — clave presente, lista vacía. Proyectos generados **no** heredan los enforcement patterns del meta-repo; el loader devuelve `PreWriteRules(())` (no `None`).
- `skills_allowed` — clave **omitida** en el template. Loader devuelve `None` (deferred), reflejando el estado del meta-repo hasta que se pueble la allowlist por proyecto.
- `lifecycle.pre_compact.persist` — los 3 items canónicos (`decisions_in_flight`, `phase_minus_one_state`, `unsaved_pattern_candidates`).
- `lifecycle.post_merge.skills_conditional[0].trigger` — globs genéricos conservadores (`src/**`, `lib/**`, `*.py`, `package.json`, `pyproject.toml`) + `skip_if_only` para docs + `min_files_changed: 2`. Suficiente para que `post_merge_trigger()` devuelva un dataclass tipado; los proyectos afinan cuando estabilicen convenciones.

Contrato lockdown: `bin/tests/test_template_loader_contract.py` corre los 5 accessors del loader real contra el output del generador real sobre los 3 profiles canónicos (cli-tool, nextjs-app, agent-sdk). Cualquier regresión del template que rompa el shape esperado se detecta ahí — no hay TS-side reimplementation del contrato.

Selftest cleanup: `bin/_selftest.py` removió los overlays de D4 y D5 (template ahora emite baseline matching). D3 y D6 mantienen overlays mínimos por diseño explícito (A1 emite `enforced_patterns: []` + A2 omite `skills_allowed`); el comentario en cada escenario documenta la razón.

Ver [MASTER_PLAN.md § Rama F3b](../../MASTER_PLAN.md), [ROADMAP.md fila refactor/template-policy-d5b-migration](../../ROADMAP.md), [HANDOFF.md §1](../../HANDOFF.md), [docs/ARCHITECTURE.md § 10 Selftest end-to-end](../../docs/ARCHITECTURE.md).

## Sexto hook entregado — `hooks/pre-compact.py` (Rama D6)

Segunda aplicación del patrón **informative** (PreCompact) tras D2. Shape idéntico a `session-start.py`: exit 0 siempre, nunca `permissionDecision`, safe-fail graceful sobre payload malformado.

- Lee `policy.yaml.lifecycle.pre_compact.persist` vía `pre_compact_rules(cwd)`. Emite `hookSpecificOutput.additionalContext` con checklist de items a persistir antes de que `/compact` trunque la conversación. El caso de uso es prompt-engineering al modelo (reminder declarativo), no enforcement — bloquear un `/compact` user-invoked sería destructivo.
- Trigger `auto`/`manual` (campo del payload) registrado en el log pero sin efecto sobre la salida: la checklist es la misma en ambos caminos. Los tests lo verifican explícitamente (`test_auto_and_manual_triggers_produce_same_output`).
- Failure mode (c.2) canonical — misma política que los 3 consumidores del loader: `policy.yaml` missing / malformed / sin sección `pre_compact` → log `status: policy_unavailable` + `additionalContext` mínimo `"pos pre-compact: policy unavailable (...)"`. Nunca deny blind.
- Safe-fail informative (excepción canonical D2): stdin vacío / JSON inválido / top-level no-dict / lista / escalar → exit 0 + `additionalContext` `"(error reading payload: ...)"` + log `status: payload_error`. Nunca `permissionDecision`, nunca exit 2.
- Double log: `pre-compact.jsonl` siempre; `phase-gates.jsonl` evento `pre_compact` **sólo en happy path** (los caminos `policy_unavailable` y `payload_error` quedan sólo en el hook log — la puerta del lifecycle no se cruza sin checklist real emitido). Campos del hook log: `{ts, hook, trigger, status, ...}`; en happy path añade `persist_count: <int>`.
- Reuso `_lib/`: `policy.pre_compact_rules` + `append_jsonl` + `now_iso`. Sin helpers privados dignos de extracción.
- Tests: 25 casos en `hooks/tests/test_pre_compact.py` (6 clases: `TestOutputEnvelope`, `TestHappyPath`, `TestFailureMode`, `TestSafeFailInformative`, `TestLogging`, `TestMainInProcess`). Fixtures: `pre_compact_auto.json`, `pre_compact_manual.json`. Extensión de `fixtures/policy/full.yaml` con bloque `lifecycle.pre_compact.persist: [decisions_in_flight, phase_minus_one_state, unsaved_pattern_candidates]`.

## Séptimo hook entregado — `hooks/stop-policy-check.py` (Rama D6)

Cuarta aplicación del patrón **blocker** (Stop) — shape idéntico a D1/D3/D4 (safe-fail canónico con deny-on-malformed) pero **scaffold activable, NO enforcement en producción hoy**. Enforza skill-allowlist contra `policy.yaml.skills_allowed`.

**Framing — regla dura para evitar sobrerrepresentación**: el hook está montado y su cadena de enforcement existe end-to-end en código + tests, pero `policy.yaml.skills_allowed` todavía no existe en el meta-repo, así que toda invocación real en prod degrada a `status: deferred` pass-through. **No presentar Stop como enforcement útil hoy**. Los tests que ejercen deny-path existen para lock-down del contrato, no como guardias operativos. Cuando E1a (o posterior) declare `skills_allowed` + provea el logger de `.claude/logs/skills.jsonl` (la primera skill que escriba ahí será `/pos:kickoff`), enforcement se activa sin refactor.

- Contrato de cuatro caminos de decisión (tri-estado de `skills_allowed_list` + malformed):
  1. `policy.yaml` missing/malformed → log `status: policy_unavailable`, pass-through exit 0. Mismo shape que los otros hooks post-D5b.
  2. `policy.yaml` OK pero sin clave `skills_allowed` → log `status: deferred`, pass-through exit 0. **Estado actual de prod**.
  3. `skills_allowed` presente pero mal formada (escalar, lista con no-strings, dict) → accessor devuelve el sentinel `SKILLS_ALLOWED_INVALID` → log `status: policy_misconfigured`, pass-through exit 0. **Distinto de deferred**: un typo en la policy NO apaga enforcement silenciosamente; el status es observable en el hook log.
  4. `skills_allowed` declarado como lista válida (puede ser `[]` = deny-all) → invocaciones filtradas por `session_id` del payload Stop; deny exit 2 con primer violador + guía `"Add it to the allowlist or revert the invocation."` en `decisionReason`; sin violaciones → allow exit 0.
- Session scoping (post-review): `_extract_invoked_skills(repo_root, session_id) → list[str]` stream-parsea `.claude/logs/skills.jsonl` línea a línea (memoria acotada) y cuenta **solo** entradas cuyo `session_id` coincide con el payload actual. Entradas sin `session_id`, con session_id no-string, o de sesiones anteriores se ignoran — el log es append-only y se contamina entre sesiones. Si el payload Stop carece de `session_id` (o no es string/está vacío) → safe-fail deny (no se puede scopiar enforcement).
- Fuente de invocaciones: `.claude/logs/skills.jsonl` — canonical audit log declarado en `policy.yaml.audit.required_logs`. Las entradas **deben** traer `session_id` + `skill` strings para ser contabilizadas. El hook es enforcer, no forense: líneas non-JSON, entries non-dict, campos mal tipados → silencio + skip (no crash).
- Helper `_validate(invoked: list[str], allowed: tuple[str, ...]) → tuple[str, list[str]]` devuelve `("deny", violations)` si cualquier invoked no está en el allowlist, else `("allow", [])`. Allowlist vacía (`()`) deniega cualquier invocación por construcción (deny-all explícito es política válida); allowlist vacía + cero invocaciones → allow.
- Safe-fail blocker canonical (D1/D3/D4): stdin vacío / JSON inválido / top-level no-dict / `session_id` ausente o no-string → deny exit 2 con `permissionDecision: deny` + `decisionReason` explicando la malformación. El hook no puede dejar pasar lo que no puede validar.
- Double log **sólo en decisiones reales**: `stop-policy-check.jsonl` (`{ts, hook, session_id, decision, violations, reason}` en deny; `{ts, hook, session_id, decision: allow, invoked_count}` en allow) + `phase-gates.jsonl` evento `stop` (con `session_id` + `decision: allow|deny`). Los status advisory (`deferred`, `policy_misconfigured`, `policy_unavailable`) quedan sólo en el hook log — la puerta del lifecycle no se cruza hasta que enforcement está realmente activa.
- Reuso `_lib/`: `policy.load_policy` + `policy.skills_allowed_list` + `policy.SKILLS_ALLOWED_INVALID` + `append_jsonl` + `now_iso`. `_extract_invoked_skills` y `_validate` son privados específicos del dominio Stop — no se repiten en otros hooks, no migran a `_lib/` (regla #7: ≥2 consumidores antes de extraer).
- Tests: 55 casos en `hooks/tests/test_stop_policy_check.py` (10 clases: `TestOutputEnvelope`, `TestDeferredMode`, `TestActivableEnforcement`, `TestSessionScoping`, `TestMisconfiguredPolicy`, `TestSafeFailBlocker`, `TestLogging`, `TestMainInProcess`, `TestExtractInvokedSkillsUnit`, `TestValidateSkillsUnit`). Fixture `stop.json` con `session_id: test-session`. Helper `write_skills_allowed(repo, allowed)` + `seed_skills_log(repo, skills, session_id="test-session")` — tests multi-sesión mezclan `session_id` explícitos para cerrar el caso regresivo "rogue skill de sesión anterior contamina Stop actual". El module docstring del test file reitera el framing anti-sobrerrepresentación.

Suite global `hooks/**` tras D6 (post-review): **575 passed + 1 skipped** (D1+D2+D3+D4+D5+D5b+D6), sin regresión.

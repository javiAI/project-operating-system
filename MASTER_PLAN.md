# MASTER_PLAN — project-operating-system

> Fuente de verdad ejecutable. Cada rama tiene scope fijo, Fase -1, criterio de salida. No añadir scope a ramas en vuelo — o se refina el plan o se crea rama nueva.

## §1. Convenciones

- **Slug de rama**: `<tipo>/<fase-id>-<nombre-corto>` — ej. `feat/a-skeleton`, `feat/d1-hook-branch-gate`.
- **Marker de aprobación**: `.claude/branch-approvals/<slug-sanitized>.approved`. Sanitized = slashes → underscores.
- **Kickoff block**: primer commit de cada rama, bloque `## Kickoff` con: scope, archivos, risks, test plan, docs plan. Hook lo valida.
- **PR target**: `main`. No feature branches de >5 días sin razón documentada.

## §2.1 Fase -1 (gate, obligatoria)

Antes de crear rama, emitir:

1. **Resumen técnico** (≤300 palabras): qué archivos tocamos, qué librerías añadimos, qué hooks/skills entran, qué tests.
2. **Resumen conceptual** (≤150 palabras): por qué esta rama ahora, qué desbloquea, qué NO incluye.
3. **Ambigüedades** (lista): cualquier duda ≥10% de incertidumbre sobre scope o implementación.
4. **Alternativas evaluadas**: al menos 2, con por qué se descartaron.
5. **Test plan**: qué se testea unit, integration, selftest, CI.
6. **Docs plan**: qué archivos docs se actualizan dentro de la rama.

Esperar aprobación explícita del usuario. Con OK → crear marker + rama.

---

## FASE A — Skeleton & bootstrap

### Rama A — `feat/a-skeleton`

**Status**: ✅ COMPLETADA (esta misma sesión, pre-bootstrap)

**Scope**:
- `git init` + `.gitignore` + `README.md`
- `.claude-plugin/plugin.json`
- `CLAUDE.md` meta-repo (<200 líneas)
- `.claude/rules/*.md` (7 rules path-scoped)
- `.claude/settings.local.json`
- `policy.yaml`
- `MASTER_PLAN.md` (este archivo)
- `ROADMAP.md`, `HANDOFF.md`, `AGENTS.md`
- `docs/ARCHITECTURE.md`, `docs/SAFETY_POLICY.md`, `docs/TOKEN_BUDGET.md`, `docs/KNOWN_GOOD_MCPS.md`
- `.gitkeep` en dirs vacíos

**Excepción**: se ejecutó sin Fase -1 formal porque es el bootstrap que CREA la propia Fase -1. Todas las ramas subsiguientes la respetan.

**Criterio de salida**:
- `ls -la` muestra estructura completa.
- `CLAUDE.md` <200 líneas.
- `policy.yaml` parseable por YAML 1.2.
- `plugin.json` parseable por JSON schema.

---

## FASE B — Cuestionario + profiles + generador esqueleto

### Rama B1 — `feat/b1-questionnaire-schema` ✅ PR #1

**Scope**: `questionnaire/schema.yaml` + `questionnaire/questions.yaml` + tests schema (vitest). Sin generador todavía.

**Contexto a leer**:
- [docs/ARCHITECTURE.md § Cuestionario](docs/ARCHITECTURE.md#cuestionario)
- [.claude/rules/generator.md](.claude/rules/generator.md)

**Criterio de salida**: `npx tsx tools/validate-questionnaire.ts` valida ambos archivos. Tests >90% coverage.

### Rama B2 — `feat/b2-profiles-starter` ✅

**Scope**: `questionnaire/profiles/nextjs-app.yaml`, `agent-sdk.yaml`, `cli-tool.yaml`. Cada profile responde ~60% del cuestionario (parcial por diseño; omite los 3 campos user-specific). Añade `tools/lib/profile-validator.ts` + `tools/validate-profile.ts` (CLI) + fixtures valid/invalid + CI step `Validate profiles`.

**Ajuste vs plan original**: los fixtures viven en `tools/__fixtures__/profiles/` (no en `generator/__fixtures__/profiles/`) porque el generador no existe todavía. Consolidación diferida a B3 si aplica.

**Brechas conocidas** (diferidas a B3):

- `answer-value-not-in-array-allowlist` no se valida a nivel de instancia (ArrayField.values existe en schema).
- Campos `enum` con valor array/objeto emiten `answer-value-not-in-enum` en lugar de `answer-type-mismatch` (taxonomía imprecisa, reporting subóptimo).

**Criterio de salida**: los 3 profiles validan contra el schema de B1 (`npm run validate:profiles` exit 0). Fixtures válidos + inválidos cubren los 5 issue kinds del validator. Tests >90% coverage.

### Rama B3 — `feat/b3-generator-runner`

**Scope**: `generator/run.ts` (CLI entrypoint), `generator/lib/profile-loader.ts`, `generator/lib/schema.ts` (re-export desde `tools/lib/`), `generator/lib/validators.ts` (`completenessCheck`). Sólo runner + validación. Sin renderers aún.

**Ajuste vs plan original**: `generator/lib/token-budget.ts` **diferido**. Motivo: `questionnaire/schema.yaml` no declara `workflow.token_budget` todavía; implementar el checker sin campo que leer sería abstracción prematura (CLAUDE.md regla #7). Reintroducir en rama posterior cuando el schema añada el campo. Mismo patrón de diferimiento que las 2 brechas de B2.

**Ajuste en `generator/lib/schema.ts`**: re-exporta `parseSchemaFile` / `parseProfileFile` / `validateProfile` desde `tools/lib/` en lugar de duplicar los zod schemas. 3ª aplicación de pattern-before-abstraction (la 2ª fue `tools/lib/read-yaml.ts` en B2). Si aparece una 4ª aplicación que exija lógica generator-only, se bifurcará entonces.

**Flags diferidos**: `--out` y `--dry-run` se rechazan explícitamente con exit 2 + mensaje `flag --X not supported in B3; planned for C1`. Evita falsa sensación de funcionalidad mientras renderers no existen.

**Semántica de exit codes**: profile con answers inválidos → exit 1; profile parcial con solo `identity.name`/`description`/`owner` faltantes → exit 0 + warning en stdout dentro del reporte (son user-specific, se resuelven en runner interactivo de fase posterior); otros required-missing → exit 1; I/O o args → exit 2.

**Criterio de salida**: `npx tsx generator/run.ts --profile ... --validate-only` retorna 0/1 según validez. Coverage 85%.

---

## FASE C — Templates + renderers

### Rama C1 — `feat/c1-renderers-core-docs`

**Scope**: renderers para `CLAUDE.md`, `MASTER_PLAN.md`, `ROADMAP.md`, `HANDOFF.md`, `AGENTS.md`, `README.md`. Templates Handlebars correspondientes. Snapshot tests + tests semánticos por renderer. Pipeline `FileWrite[]` + wire-up de `--out`/`--dry-run` en [generator/run.ts](generator/run.ts).

**Contexto a leer**:

- [docs/ARCHITECTURE.md § Generador](docs/ARCHITECTURE.md)
- [.claude/rules/generator.md](.claude/rules/generator.md) + [.claude/rules/templates.md](.claude/rules/templates.md)
- `generator/run.ts` + `generator/lib/` entregados en B3.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **User-specific placeholders**: los campos `identity.name|description|owner` faltantes en el profile no bloquean el render. El renderer inyecta literal `TODO(identity.<campo>)` + warning. Aplica tanto a `--dry-run` como a `--out`. Sustitución final pasará por el runner interactivo de fase posterior.
- **Carry-over Fase N+7 parcial**: en C1 solo cubre `templates/HANDOFF.md.hbs` (matriz de decisión + checklist post-merge) y `templates/AGENTS.md.hbs` (Fase N+7 en flujo de rama). `templates/.claude/rules/docs.md.hbs` **diferido a C2** por coherencia con el scope de C2 (`.claude/rules/*.md`).
- **`--out` con subdirectorios** desde el primer día. El pipeline trabaja con `FileWrite.path` relativo + `mkdir -p` — evita refactor en C2..C5.
- **`FileWrite` shape mínimo**: `{ path: string; content: string }`. Sin `mode`. Los bits de permisos se añaden en C5 (`feat/c5-renderers-skills-hooks-copy`) cuando la copia de hooks ejecutables los requiera.
- **`render-pipeline`** falla explícitamente ante colisión de paths (no sólo lo detecta en tests). Invariante: cada `path` del `FileWrite[]` combinado es único.
- **Snapshots + tests semánticos**: snapshots por (profile × template) = 18, pero además tests unitarios por renderer verifican paths emitidos y strings críticas (ej. "Fase N+7" en HANDOFF, "Kickoff block" en CLAUDE). Snapshots no son la única red de seguridad.
- **`--validate-only`** conservado por compat/transición. Sin flags = comportamiento validate-only. `--force` queda fuera de scope C1.

**Deps nuevas**: `handlebars` (única).

**Criterio de salida**: `npx tsx generator/run.ts --profile <canonical> --out <tmpdir>` emite el árbol esperado de 6 docs + placeholders visibles cuando aplique. `--dry-run` lista paths sin tocar fs. Snapshots estables (re-run byte-equal). Coverage ≥85%. CI verde.

### Rama C2 — `feat/c2-renderers-policy-rules` ✅

**Scope**: renderer para `policy.yaml` + `.claude/rules/*.md` (según stack/paths del profile). Templates + helpers Handlebars.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Composición de renderers en `generator/renderers/index.ts`, no en `run.ts`**: estructura con tres arrays congelados (`coreDocRenderers` + `policyAndRulesRenderers` + `allRenderers`). `run.ts` importa sólo `allRenderers` y permanece fino; futuras ramas (C3, C4, C5) crean array propio y lo componen dentro de `allRenderers` sin tocar `run.ts`. Evita que el runner se convierta en sitio de composición creciente.
- **Scope de rules acotado a `docs.md` + `patterns.md`**: no se incluyen `generator.md` / `templates.md` / `tests.md` / `ci-cd.md` / `skills-map.md`. Se añadirán en ramas posteriores sólo si aparece señal de stack-specificidad real.
- **`policy.yaml` por un solo renderer con un solo template Handlebars**: no se fragmenta por secciones. Conditionals stack inline (`{{#if (eq answers.stack.language "typescript")}}`) cubren `pre_push.checks_required` y `testing.unit.framework_node|framework_python`.
- **`type: "generated-project"` hardcoded** en el template (nunca depende del profile). **`project:` vía `{{answers.identity.name}}`** — expande a `TODO(identity.name)` mientras los 3 paths user-specific no estén resueltos (patrón heredado de C1).
- **Carry-over Fase N+7 cerrado**: `templates/.claude/rules/docs.md.hbs` incluye el bullet "Trazabilidad de contexto" referenciando `HANDOFF.md §3` (diferido desde C1 por coherencia de scope con `.claude/rules/*.md`).
- **Comentarios decorativos preservados** en `policy.yaml.hbs` (separadores `─` y cabeceras de sección). El render final mantiene la legibilidad del policy canónico del meta-repo.

**Deps nuevas**: ninguna (reuso de `handlebars` + `yaml` ya presentes).

**Criterio de salida** (cumplido): 9 `FileWrite` por profile (6 docs C1 + `policy.yaml` + `.claude/rules/docs.md` + `.claude/rules/patterns.md`), `yaml.parse(policy.yaml)` OK sobre los 3 canónicos, stack conditionals mutuamente exclusivos (no leaks), 27 snapshots (3 profiles × 9 templates) byte-estables entre runs, coverage ≥85%, CI verde.

### Rama C3 — `feat/c3-renderers-tests-harness` ✅

**Scope**: renderer para test harness según stack (Node/Python/Go/Rust). Configs (vitest, jest, pytest, cargo, go.mod), README de tests, ejemplo smoke test.

**Ajustes vs plan original** (Fase -1 aprobada):

- Scope reformulado a **"test harness mínimo generado y estructuralmente coherente"** — no se promete ejecución real end-to-end. `package.json` (TS), `pyproject.toml` (Python) y `playwright.config.ts` quedan **fuera de C3** (diferidos). El `tests/README.md` emitido documenta el gap ("Qué NO emite C3").
- Combinaciones soportadas: **`typescript+vitest`** y **`python+pytest`** únicamente (los 2 que aparecen en profiles canónicos). `jest`, `go-test`, `cargo-test` **diferidos con fallo explícito y testeado** dentro de `renderTests(...)`: el `Error` menciona el nombre concreto del framework, la palabra "deferred" y el path `testing.unit_framework` — no se mueve a `run.ts`. Razón: CLAUDE.md regla #7 (0 repeticiones documentadas).
- `testsHarnessRenderers` como grupo de **1 renderer único** (no fragmentado por archivo emitido). El renderer devuelve 4 `FileWrite` según la combinación stack+framework. Consistente con `policyAndRulesRenderers` (1 renderer puede emitir varios paths si la condición gobierna el set).
- **`Makefile` universal** (TS + Python) como entry-point común (`make test` / `test-unit` / `test-coverage` / `test-e2e` placeholder / `clean`). No se emite `package.json.scripts`. Los workflows C4 deberán invocar `make test-*` (no `npx vitest` / `pytest` directos).
- **`valid-partial` fixture modificada**: añadidos `testing.coverage_threshold: 80` + `testing.e2e_framework: "none"` explícitos. Razón: `buildProfile` no materializa defaults del schema; los templates C3 los referencian. Defaults-in-profile queda diferido.
- **Tests adicionales del plan original** (requeridos en Fase -1): trailing `\n` en todos los FileWrite emitidos; TS sin rastro de `pytest`; Python sin rastro de `vitest`; 1 test por framework diferido (no aggregated).
- **`.claude/rules/tests.md` NO tocado** — expandirlo sin señal nueva sería ruido (guidance explícita Fase -1). La rule existente cubre la expectativa de patrón renderer-group + snapshot testing.

### Rama C4 — `feat/c4-renderers-ci-cd` ✅

**Scope**: renderer para `.github/workflows/ci.yml` + `docs/BRANCH_PROTECTION.md` (dinámico). 4ª aplicación del patrón `renderer-group`.

**Ajustes vs plan original** (Fase -1 aprobada):

- **Solo `ci.yml`** (A1). `audit.yml` y `release.yml` quedan fuera de scope (release.yml depende de `workflow.release_strategy` con lógicas divergentes → rama posterior).
- **Runtime versions hardcoded** (A2): Node `20.17.0` + Python `3.11`. Deuda documentada como rama futura (*schema: añadir `stack.runtime_version`*) en `.claude/rules/generator.md § Deferrals`. Comentario breve en el template, no ensayo.
- **Coverage gate delegado al `Makefile` C3** (A3): el workflow invoca `make test-unit` y `make test-coverage` sin duplicar thresholds.
- **`BRANCH_PROTECTION.md` dinámico** (A4): lista los jobs del `ci.yml` emitido (consistencia cruzada testeada).
- **`ci_host ∈ {gitlab, bitbucket}` → `Error` explícito** (A5) dentro del renderer (host + `deferred` + path `workflow.ci_host`), mismo patrón que frameworks diferidos de C3. Razón: 0 repeticiones documentadas, CLAUDE.md #7.
- **`branch_protection == false` → sólo `ci.yml`** (A6). No se emite `docs/BRANCH_PROTECTION.md` cuando la protección está desactivada.
- **Python toolchain minimal** (ajuste explícito del usuario): `actions/setup-python` + `pip install pytest pytest-cov`. Sin `uv`/`poetry`/`pdm` — coherente con C3 que no emite `pyproject.toml`. Preferencia fuerte de toolchain se difiere hasta una rama que la haga justificable desde el output actual del proyecto generado.
- **Composición en `generator/renderers/index.ts`, no en `run.ts`** (heredado de C2/C3): nuevo array congelado `cicdRenderers` compuesto en `allRenderers`. `run.ts` intacto.
- **Fixture `valid-partial` actualizado** con `workflow.ci_host` + `workflow.branch_protection` explícitos (workaround heredado de C3 por `buildProfile` sin materialización de defaults).
- **Branch protection se aplica manualmente**: el doc markdown describe la configuración recomendada; el generador no llama a la GitHub API (control-plane vs runtime-plane, ARCHITECTURE.md §1).

**Criterio de salida** (cumplido): 15 `FileWrite` por profile (9 C1+C2 + 4 C3 + 2 C4), `yaml.parse(ci.yml)` OK sobre los 3 canonicals, SHA40 pins en todas las `uses:`, mutual-exclusión de stack conditionals, 45 snapshots estables, coverage ≥85%, CI verde.

### Rama C5 — `feat/c5-renderers-skills-hooks-copy` ✅

**Scope original**: renderer que copia `skills/` + `hooks/` del plugin al proyecto generado, ajustando paths y permisos.

**Scope entregado (recortado en Fase -1)**: renderer único `skills-hooks-skeleton.ts` que emite **solo la estructura** del directorio `.claude/` del proyecto generado: `.claude/settings.json` (`hooks: {}` + `_note` de deferral; **sin** `permissions` baseline) + `.claude/hooks/README.md` (documenta deferral a Fase D) + `.claude/skills/README.md` (documenta deferral a Fase E). 3 FileWrite por profile; 18 archivos totales por profile (15 C1–C4 + 3 C5).

**Lo que C5 NO hace** (explícito por docs-sync):

- **No copia real de hooks ejecutables**. Razón: `hooks/` del meta-repo no existe todavía; copiar placeholders sería abstracción prematura (CLAUDE.md regla #7). Diferido a rama post-D1 cuando exista el catálogo estable.
- **No copia real de skills**. Razón: las skills del plugin viven en un catálogo en evolución activa; una instantánea copiada hoy garantiza drift inmediato. Diferido a rama post-E1a cuando el catálogo esté auditado (`/pos:audit-plugin --self` green).
- **No extiende `FileWrite` con `mode`**. Razón: mientras `pos` no emita ejecutables reales, `{ path, content }` basta. La extensión a `{ path, content, mode? }` llegará en la misma rama que copie ejecutables.

**Ajustes vs plan original** (Fase -1 aprobada):

- **Scope recortado** (decisión explícita del usuario): solo esqueleto, cero copia real. Evita mezclar alcance C con alcance D/E.
- **Renderer naming**: `skills-hooks-skeleton.ts` (no `settings-skeleton.ts`) — el nombre refleja el dominio real del directorio emitido, aunque el scope actual sea estructural.
- **`.claude/settings.json` mínimo conservador**: solo `hooks: {}` + `_note`. **Sin** `permissions` baseline; esa decisión la toma Fase D cuando los hooks reales definan su superficie.
- **Patrón `renderer-group` 5ª aplicación** (`skillsHooksRenderers` frozen compuesto en `allRenderers`). `run.ts` intacto.
- **Docs-sync explícito sobre los 3 deferrals** (copia hooks, copia skills, `FileWrite.mode`). Ver [HANDOFF.md §10](HANDOFF.md), [.claude/rules/generator.md § Deferrals](.claude/rules/generator.md).

**Criterio de salida** (cumplido): 18 `FileWrite` por profile (15 C1–C4 + 3 C5), `JSON.parse(settings.json)` OK sobre los 3 canonicals con `hooks === {}` y `_note` string, READMEs documentan deferral (`/pos/` + `/Fase\s*D|E/` + `/diferid/i`), contenido stack-agnostic (sin leaks vitest/pytest/npm/pip), 54 snapshots estables (45 previos + 9 nuevos), `validate:generator` + `render:generator` exit 0, vitest 515/0.

---

## FASE D — Hooks (Python)

### Rama D1 — `feat/d1-hook-pre-branch-gate`

**Status**: ✅ COMPLETADA (PR pendiente).

**Scope entregado**: `hooks/pre-branch-gate.py` + test pair pytest + bootstrap test env (`.venv` + `requirements-dev.txt`). Bloquea `git checkout -b`, `git switch -c`, `git worktree add -b` sin marker `.claude/branch-approvals/<sanitized-slug>.approved`. `permissionDecision: deny` + exit 2 con `decisionReason` informativo (ruta marker + `touch` sugerido + ref textual a `MASTER_PLAN.md`). Pass-through silencioso en el resto. Double log: `.claude/logs/pre-branch-gate.jsonl` + `.claude/logs/phase-gates.jsonl` (evento `branch_creation`).

**Referencia**: ver [master_repo_blueprint.md](master_repo_blueprint.md) y el homólogo del repo de referencia (mentalmente; NO copiar literal).

**Ajustes vs plan original** (Fase -1 aprobada):

- **Alcance ampliado**: además del `checkout -b` / `switch -c` del plan original, cubre también `git worktree add -b` (bypass obvio que el plan no cubría). `git branch <slug>` deliberadamente excluido (ref sin checkout, no inicia trabajo).
- **Sin bypass env var** (rechazado `POS_SKIP_BRANCH_GATE=1`). Bypass legítimo = crear marker explícito.
- **Parsing con `shlex.split`** (robusto a quoting + global options git pre-subcommand: `git -c k=v ...`, `--git-dir=X`, `-C /path`).
- **Double log** desde D1 (`pre-branch-gate.jsonl` + `phase-gates.jsonl`): prepara `/pos:audit-session` (F3) sin refactor posterior.
- **Mensaje al bloquear** con `decisionReason` que incluye ruta del marker, `touch` sugerido, y referencia textual a `MASTER_PLAN.md`. Sin parseo del plan ni inferencia de sección específica.
- **Sin `hooks/_lib/` compartido**: CLAUDE.md regla #7 (≥2 reps antes de abstraer). D1 es la primera repetición; D2 (`session-start`) será la señal para extraer helpers (`sanitize_slug`, `append_jsonl`, `now_iso`).
- **Bootstrap de test env dentro de esta rama**: `.venv` + `requirements-dev.txt` (solo `pytest>=7` + `pytest-cov>=4`). `.gitignore` añade entradas Python (`/.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.coverage`). **Sin ruff**, **sin `bin/pos-selftest.sh`** (ambos explícitamente fuera de scope D1).
- **In-process tests añadidos** (+32 sobre los 23 subprocess): pytest-cov no mide subprocesses; se cargan el módulo vía `importlib.util.spec_from_file_location` (por guión en el nombre del archivo) y se invoca `main()` con `monkeypatch` de `sys.stdin` + `chdir`. 60 tests total, 99% coverage (única línea no cubierta: `sys.exit(main())` bajo `__main__` guard).
- **`.claude/settings.json` no modificado**: ya referenciaba `./hooks/pre-branch-gate.py` desde Fase A. D1 sólo materializa el binario ausente.
- **Review follow-up** (post-PR #11, Copilot + feedback humano):
  - Validación de `tool_input`: si es `null` → `{}` (pass-through); si no es `dict` → `deny` exit 2. Evita `AttributeError` en payloads malformados con `tool_input` lista/string.
  - Contract de stdin explicitado en `docs/ARCHITECTURE.md §7` y `.claude/rules/hooks.md`: payload malformado (stdin vacío, JSON inválido, top-level no-dict, `tool_input` no-dict) → `deny` exit 2 con `decisionReason`, no pass-through. Política safe-fail ahora canónica para todos los hooks.
  - CI: nuevo job `python` en `.github/workflows/ci.yml` (matriz ubuntu + macos × Python 3.10/3.11, pytest + coverage). D1 pasa a estar cubierto por CI real, no sólo por pytest local. Alineado con `.claude/rules/ci-cd.md §Workflows obligatorios §1`.

### Rama D2 — `feat/d2-hook-session-start`

**Status**: ✅ COMPLETADA (PR pendiente).

**Scope entregado**: `hooks/session-start.py` — snapshot 30s (branch / phase / last merge / warnings) como `hookSpecificOutput.additionalContext` en cada `SessionStart` (source `startup` / `resume` / `clear` / `compact`). Double log: `.claude/logs/session-start.jsonl` (shape propio) + `.claude/logs/phase-gates.jsonl` (evento `session_start`). Hook informativo: nunca bloquea — payload malformado o git indisponible degradan a snapshot mínimo + log de error, exit 0 siempre. En paralelo: extracción de `hooks/_lib/` (segunda repetición de CLAUDE.md regla #7) con rewire de D1 en el mismo PR.

**Ajustes vs plan original** (Fase -1 aprobada con decisiones A1/B1/C1/E1/F/G/H1/I):

- **Extracción `hooks/_lib/` ejecutada en este PR** (decisión A1): `slug.sanitize_slug`, `jsonl.append_jsonl`, `time.now_iso`. `_lib/__init__.py` vacío (package marker). D1 rewireado en el mismo commit de refactor: sus 60 tests siguen verdes (re-export `pbg.sanitize_slug` preservado). No se extrae helper de git subprocess — `_git` permanece local a `session-start.py` hasta que un segundo hook lo reuse (regla #7, primera repetición).
- **Imports sin package formal** (decisión B1): `sys.path.insert(0, str(Path(__file__).parent))` + `from _lib.X import Y  # noqa: E402` en ambos hooks. El nombre hyphenated no es importable como módulo; `_lib` sí (package). Sin renombrar los hooks ni crear setup.py.
- **Derivación de fase híbrida** (decisión C1): regex `^(feat|fix|chore|refactor)[/_]([a-z])(\d+)-` sobre nombre de rama (case-insensitive; salida canónica `[A-Z]\d+`, p.ej. `D2`). En `main`/`master` fallback a `.claude/logs/phase-gates.jsonl` con recorrido hacia delante conservando la última fase parseable (streaming O(1) memoria). `unknown` si ninguna fuente resuelve. No se parsea `ROADMAP.md` ni `MASTER_PLAN.md` (evita acoplamiento + coste).
- **Warning docs-sync** (decisión E1): se emite cuando `git diff --name-only main...HEAD` no incluye `ROADMAP.md` ni `HANDOFF.md`. Suprimido cuando la rama es `main`/`master` y cuando git no está disponible (evita falsos positivos en repos recién clonados o sin `main`).
- **Warning marker ausente** (decisión F): se emite cuando `.claude/branch-approvals/<sanitized-slug>.approved` no existe sobre cualquier rama distinta de `main`/`master` (slug sanitizado vía `_lib.slug.sanitize_slug`, idéntico al de `pre-branch-gate`). Suprimido en `main`/`master`.
- **Safe-fail informativo canonicalizado** (decisión G): excepción explícita a la política general de blocker hooks (D1/D3/D4/D6). `SessionStart` es informativo por naturaleza — degradar a snapshot mínimo + log de error es preferible a exit 2, que dejaría al usuario sin contexto. Matización añadida a `.claude/rules/hooks.md` y `docs/ARCHITECTURE.md §7 Capa 1`.
- **Sin diferenciación por `source`** en el output del snapshot (decisión H1): `startup` / `resume` / `clear` / `compact` producen el mismo payload. El `source` se loggea en `session-start.jsonl` y `phase-gates.jsonl` para futuros análisis (F3 `/pos:audit-session`), pero no modula el texto emitido al LLM. Simplicidad > personalización prematura.
- **Subprocess git robusto** (decisión I): `_git(cwd, *args)` con `shell=False`, `cwd=` explícito, `timeout=2`, `check=False`. Captura `FileNotFoundError` (git no instalado) + `subprocess.SubprocessError` (timeout/interrupt). Return `None` en cualquier error; el caller decide degradación. Ningún camino sube excepción.
- **Snapshot ≤10 líneas** (ajuste del usuario sobre el plan original): prosa mínima, formato determinista (`pos snapshot` header + 4 líneas fijas + bloque de warnings opcional). `Warnings: (none)` cuando no hay warnings para evitar ambigüedad de ausencia. Contenido estrictamente útil, sin repetir info derivable del propio Claude Code (session_id, tools disponibles, etc.).
- **Sin `hooks/tests/test_lib/`** (ajuste del usuario): `_lib/` se testea únicamente via los tests de los hooks que lo consumen. Lógica trivial (una línea por función); crear suite paralela sería sobreingeniería. Regla #7 aplica también a tests: la justificación vendría sólo si `_lib/` creciera a lógica no trivial.
- **Test pattern replicado de D1**: 66 tests nuevos (subprocess + in-process via `importlib.util.spec_from_file_location`). `TestMainInProcess` añadió 5 tests post-GREEN para cubrir los caminos git (subprocess tests no son visibles a pytest-cov). Coverage final: 95% sobre `session-start.py`, 99% combinado.
- **`.claude/settings.json` no modificado**: ya referenciaba `./hooks/session-start.py` desde Fase A (mismo patrón que D1).

**Criterio de salida**: 126 tests verdes (60 D1 intactos + 66 D2), coverage ≥80% lines / ≥75% branches (alcanzado 99% combinado), `_lib/` consumido por al menos 2 hooks (D1 + D2) con tests de ambos pasando, docs-sync en el propio PR (ROADMAP + HANDOFF + MASTER_PLAN + ARCHITECTURE + `.claude/rules/hooks.md`), hook instalado (snapshot visible al arrancar una nueva sesión). Cumplido.

### Rama D3 — `feat/d3-hook-pre-write-guard`

**Scope (entregado)**: `hooks/pre-write-guard.py` — PreToolUse(Write) blocker que enforza test-pair sobre `hooks/*.py` top-level + `generator/**/*.ts`. Shape canónico blocker (D1), no informative (D2).

**Ajustes vs plan original** (Fase -1 aprobada):

- **Scope recortado a sólo test-pair enforcement**. El plan original mencionaba además "inyecta patterns path-scoped, bloquea anti-patterns". Ambas piezas **diferidas a rama post-E3a**: `.claude/patterns/` y `.claude/anti-patterns/` están vacías hasta que `/pos:compound` las pueble en E3a; implementar inyector/bloqueador sobre dirs vacíos sería código sin datos (CLAUDE.md regla #7). D3 recortado sigue cerrando el criterio funcional de CLAUDE.md regla #3 (desbloquea TDD hard-enforced para E*).
- **Contrato explícito del hook** (crystal-clear en la suite y en `.claude/rules/hooks.md`):
  - enforced + archivo inexistente + sin test pair → deny exit 2.
  - enforced + archivo inexistente + con test pair → allow exit 0.
  - enforced + archivo ya existente → allow exit 0 (edit flow; D4 detecta pérdida de cobertura sobre impl existente).
  - excluido o fuera de scope → pass-through silencioso (cero log).
- **`generator/run.ts` queda enforced** uniforme (no se introduce excepción). Tiene `generator/run.test.ts` co-located, así que nunca bloquea hoy.
- **Clasificador con dos buckets de exclusión separados** (`.claude/rules/hooks.md`): (1) tests/docs/templates/meta; (2) helper internals `hooks/_lib/**` (decisión repo D2, motivo distinto, clase separada en la suite).
- **`file_path` ausente o no-string → pass-through** (no es malformación total del payload). Distinto de `tool_input` no-dict que sí es deny.
- **Lista de paths hardcoded**. Mover a `policy.yaml` diferido a D4 (cuando `policy.yaml` esté enforced).
- **Evento canónico en phase-gates**: `pre_write` (se suma a `branch_creation` de D1 y `session_start` de D2).
- **Sin waiver `// test-waiver: <razón>`** pese a estar mencionado en `.claude/rules/tests.md`. Ningún caso real lo demanda hoy (regla #7 — evidencia antes de abstraer).

### Rama D4 — `feat/d4-hook-pre-pr-gate`

**Scope (entregado)**: `hooks/pre-pr-gate.py` — PreToolUse(Bash) blocker sobre `gh pr create` que enforza docs-sync como único check real; scaffold advisory no-blocking para skills_required / ci_dry_run_required / invariants_check. Shape canónico blocker D1 (tercera aplicación del patrón).

**Ajustes vs plan original** (Fase -1 aprobada, recorte explícito del scope):

- **Trigger recortado a `gh pr create` únicamente**. El plan original mencionaba "matcher `gh pr create` / `git push`"; `git push` queda fuera de D4 (scope separado — reabre cuando haya señal concreta de bloqueo pre-push útil vs coste de falsos positivos). `gh pr edit`, `gh pr view`, `gh pr list`, `gh issue create` → pass-through silencioso.
- **Docs-sync como único enforcement real**. `skills_required`, `ci_dry_run_required`, `invariants_check` quedan como **advisory scaffold no-blocking** (se loguean con `status: "deferred"` en cada decisión real, sin afectar el exit code). Razón: ninguno tiene sustrato todavía — las skills reales aterrizan en Fase E*; CI dry-run requiere rama dedicada; invariants directory está vacío. Activar cualquiera de los 3 sin su sustrato sería abstracción sin datos (CLAUDE.md regla #7). El scaffold es **activable sin cambio de shape** cuando sus prerequisitos aterricen.
- **Reglas de docs-sync hardcoded en el hook** (mirror textual de `policy.yaml.lifecycle.pre_pr.docs_sync_required` + `docs_sync_conditional`). **Sin pyyaml**, sin parser declarativo. La migración a policy-driven loading queda diferida a una **rama policy-loader propia** que unificará este hardcoded con el de D3 (paths enforced). Razón: introducir un parser declarativo en D4 inflaría scope y mezclaría dos deudas distintas.
- **Divergencia deliberada — `hooks/tests/` vs policy**: el hook excluye `hooks/tests/` del trigger `hooks/** → docs/ARCHITECTURE.md`, mientras `policy.yaml.lifecycle.pre_pr.docs_sync_conditional` lista `hooks/**` uniforme. Motivo semántico: editar tests no altera arquitectura y no debe forzar docs-sync arquitectural. Los archivos de test no son implementación; cambios ahí solos no justifican tocar `ARCHITECTURE.md`. La reconciliación (cambiar la policy a granular, o aceptar la excepción en el loader) queda diferida a la **rama policy-loader**. No es un bug ni una omisión — es decisión D4 que el loader deberá interpretar cuando lea la policy.
- **Distinción empty-diff vs diff-unavailable en el flujo main**: `diff_files` devuelve `list[str] | None` (no `[]` en error). `None` → skip advisory con `status: "skipped", reason: "git diff unavailable"`; `[]` → deny con reason dedicado de empty PR. Evita false-deny cuando git subprocess falla tras merge-base OK. Tests: `TestDiffUnavailable` (5 casos, en review-PR #15).
- **Dedupe explícito de triggering docs**. `generator/**` y `.claude/patterns/**` apuntan ambos a `docs/ARCHITECTURE.md`; la entrada missing aparece una sola vez, con los paths triggering listados tras `— required by` y capados a 3 con sufijo `... (+N more)` cuando hay más.
- **Skip advisory (pass-through + log explícito) en main / master / HEAD detached / cwd no-git / `git merge-base HEAD main` no resoluble**. Decisión vs alternativa "silent skip": el log advisory aporta trazabilidad sin deny ruidoso. Skip entries van al hook log; **`phase-gates.jsonl` intacto en skips** (no son decisiones reales del lifecycle).
- **Empty diff → deny con reason dedicado separado del de docs-sync** (`"PR creation blocked: no changes between merge-base and HEAD (empty PR). Base: <sha>"`). Distinto del reason docs-sync para no sugerir al usuario que añadir docs resolvería un problema que es "no hay diff en absoluto".
- **Safe-fail blocker canonical D1** (no D2 informative): stdin vacío / JSON inválido / top-level no-dict / `tool_input` no-dict → deny exit 2. Command ausente / no-string / vacío / shlex unparsable → pass-through exit 0.
- **Evento canónico en `phase-gates.jsonl`**: `pre_pr` (se suma a `branch_creation` D1, `session_start` D2, `pre_write` D3). Entradas `deferred` advisory van sólo al hook log, no a `phase-gates.jsonl`.
- **`hooks/pre-write-guard.py` NO tocado en D4**. La migración de los paths hardcoded de D3 a `policy.yaml` se acompaña en la misma rama policy-loader que migre los de D4 (scope limpio, un cambio a la vez).
- **Reuso de `hooks/_lib/`**: `append_jsonl` + `now_iso`. Sin nuevos helpers (regla #7 aplicada incrementalmente).
- **Simplify pass explícito pre-PR** (preferencia persistente del usuario): 3 cuts aplicados — docstring 10→6 líneas, `_conditional_triggers` docstring eliminada, `missing, _triggers` → `missing, _`. Todos test-safe.
- **Trazabilidad de kickoff**: commit `e73416b` tuvo su message dañado por backticks interpretados por `$(cat <<'EOF' ...)`; follow-up `ee3099d` (empty `--allow-empty`) repone el contenido perdido sin reescribir historia.

**Criterio de salida**: 101 tests verdes (`hooks/tests/test_pre_pr_gate.py` — incluye `TestDiffUnavailable` × 5), 322 totales en `hooks/**` (D1+D2+D3+D4), coverage ≥80% lines / ≥75% branches (alcanzado ≥94% sobre `pre-pr-gate.py`, global ≥95%), `_lib/` consumido (regla #7 intacta), docs-sync en el propio PR (ROADMAP + HANDOFF + MASTER_PLAN + ARCHITECTURE + `.claude/rules/hooks.md`), hook instalado (el propio `pre-pr-gate` debe aprobar su PR al correr sobre esta rama — dogfooding). Cumplido.

### Rama D5 — `feat/d5-hook-post-action-compound` — ✅

**Status**: cerrada en rama (PR pendiente de abrir). Primera aplicación del patrón **PostToolUse non-blocking**.

**Scope entregado**: `hooks/post-action.py` — PostToolUse(Bash) hook con detección jerárquica 2 tiers (shlex command match + git reflog post-hoc confirmation). Cuando ambos tiers confirman un merge/pull local tocando paths configurados, emite `additionalContext` sugiriendo `/pos:compound`. Nunca dispatcha la skill (advisory-only; E3a entregará la skill). Exit 0 siempre — no emite `permissionDecision` bajo ningún camino.

**Contexto a leer**:

- `policy.yaml` L105-120 — `lifecycle.post_merge.skills_conditional[0]`: shape `touched_paths_any_of` + `skip_if_only` + `min_files_changed`.
- `hooks/pre-pr-gate.py` como patrón de reuso `_lib/` + safe-fail + subprocess git.
- `hooks/session-start.py` como referencia de subprocess git robusto (shell=False, cwd, timeout, check=False, catch FileNotFoundError/SubprocessError).
- `docs/ARCHITECTURE.md § 7` — capa 1 hooks canonical (blocker + informative documentados; D5 añade el tercer patrón: PostToolUse non-blocking).

**Decisiones clave (Fase -1 aprobada)**:

- **Detección jerárquica 2 tiers** en vez de matcher único. Tier 1 (`shlex.split`) clasifica comando; Tier 2 (`git reflog HEAD -1 --format=%gs`) confirma que la acción cuajó localmente. Evita falsos positivos en `git merge --abort` (Tier 1 excluye) y `git pull` que terminó siendo rebase real sin flag explícito (Tier 2 descarta `"pull --rebase"`).
- **`gh pr merge` (matcher B) descartado**. Dos razones: (a) `tool_response.exit_code` no está documentado como garantizado por Claude Code en PostToolUse(Bash) — sin él no hay forma confiable de distinguir éxito de fallo; (b) el merge se ejecuta en remoto, no deja reflog local inmediato sobre el ref local (el `pull` post-merge sí, pero eso cae en matcher C). Cerrar un caso medio roto era peor que dejarlo fuera explícitamente.
- **Scope web UI merges fuera**. Por diseño no los detectamos aquí (no hay señal local observable). Reservado para E3a `/pos:compound` como skill invocable on-demand.
- **Segunda repetición hardcoded de `policy.yaml`** (D4 = required/conditional docs-sync; D5 = post_merge skills_conditional). Regla #7 CLAUDE.md ya cumplida dos veces → precondición abierta para la rama policy-loader (post-D6) que unifique ambos parseos.
- **Advisory-only (no dispatch)**. El hook sólo emite `additionalContext` sugiriendo `/pos:compound`; nunca invoca la skill (la skill no existe todavía — llega en E3a; además invocar desde un hook es antipatrón canonizado). Mantiene separación control-plane vs skill-plane.
- **PostToolUse non-blocking canonical**. Exit 0 siempre, nunca `permissionDecision`. Payload malformado / tool_name != "Bash" / command vacío / shlex unparsable → early return 0 silencioso sin log (bloquear un PostToolUse es inviable: la acción ya ocurrió; el patrón útil es degradar a no-op). Documentado como tercer patrón canónico en `.claude/rules/hooks.md` y `docs/ARCHITECTURE.md §7`.

**Contrato fijado por la suite (4 status distinguidos)**:

1. Tier 1 miss → pass-through silencioso (cero log, cero stdout).
2. Tier 1 OK + Tier 2 fail → hook log `status: tier2_unconfirmed`; `phase-gates.jsonl` intacto (no cruzó puerta del lifecycle).
3. Tier 2 OK + diff no disponible → hook log `status: diff_unavailable`; `phase-gates.jsonl` intacto.
4. Tier 2 OK + diff OK + trigger miss → hook log `status: confirmed_no_triggers` + `phase-gates.jsonl` evento `post_merge`.
5. Tier 2 OK + diff OK + trigger match → hook log `status: confirmed_triggers_matched` + `phase-gates.jsonl` evento `post_merge` + `additionalContext` emitido.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **`gh pr merge` matcher B sacado del scope** en vez de dejarlo "medio roto" con heurísticas frágiles. Reabrir cuando `gh` deje huella local observable post-merge o Claude Code documente `tool_response.exit_code` como contrato estable.
- **Helper privado `_match(path, glob)` eliminado en simplify pass pre-PR** (preferencia persistente del usuario): era wrapper trivial sobre `fnmatch.fnmatch` con un solo caller (`match_triggers`); inlineado reduce 4 líneas sin perder legibilidad. No afecta tests (el helper era privado, no estaba en el contrato).
- **Reuso `hooks/_lib/`**: `append_jsonl` + `now_iso`. Sin nuevos helpers compartidos. Regla #7 intacta.
- **Fixture topológica two-repo** para integration tests (`repo_after_merge`, `repo_after_merge_ff`, `repo_after_pull`): upstream real + local clone + commit divergente + pull/merge real → reflog + diff auténticos. Evita mockear git en tests de integración (patrón D1/D2/D4 reforzado).
- **Test contract lock-down**: 17 clases, 110 tests ejecutados + 1 skip intencional (`TestIntegrationDiffUnavailable` delega en `TestMainInProcess` vía `pytest.skip` — subprocess no puede cubrir cleanly el camino `diff_files is None` sin romper git en el repo; el in-process con monkeypatch sí).

**Criterio de salida**: 111 tests verdes (110 + 1 skip intencional) en `hooks/tests/test_post_action.py`, 432 totales en `hooks/**` (D1+D2+D3+D4+D5), coverage ≥80% lines / ≥75% branches (alcanzado 97% lines sobre `hooks/post-action.py`, 99% sobre test_post_action.py), `_lib/` consumido (regla #7 intacta), docs-sync en el propio PR (ROADMAP + HANDOFF + MASTER_PLAN + ARCHITECTURE + `.claude/rules/hooks.md`), hook instalado (el propio `pre-pr-gate` aprueba este PR al correr sobre esta rama — dogfooding D4 sobre D5). Cumplido.

### Rama D5b — `refactor/d5-policy-loader` — ✅

**Status**: cerrada en rama (PR pendiente de abrir; docs-sync en curso). Sub-rama refactor insertada entre D5 y D6 para cumplir la precondición regla #7 CLAUDE.md abierta tras la **segunda repetición hardcoded de `policy.yaml`** en D4 + D5. Cierra la deuda antes de que D6 la triplique.

**Scope entregado**:

- `hooks/_lib/policy.py` — loader tipado con 5 dataclasses congeladas (`ConditionalRule`, `DocsSyncRules`, `PostMergeTrigger`, `EnforcedPattern`, `PreWriteRules`) + cache keyed por path abs únicamente (sin mtime/size, sin invalidación implícita por edits; `reset_cache()` para test isolation / relectura controlada) + 3 accessors (`docs_sync_rules`, `post_merge_trigger`, `pre_write_rules`) + `derive_test_pair(rel_path, label)` (2 ramas label-driven).
- `policy.yaml` — bloque nuevo `pre_write.enforced_patterns` (3 entries); `lifecycle.pre_pr.docs_sync_conditional.hooks/**` con `excludes: ["hooks/tests/**"]` (convergencia hook↔policy).
- Migración de los 3 hooks D3 / D4 / D5 a consumir el loader en el mismo PR: D3 `pre-write-guard.py` (`classify` + `derive_test_pair`), D4 `pre-pr-gate.py` (`check_docs_sync` + `_conditional_triggers`), D5 `post-action.py` (`match_triggers`).
- `requirements-dev.txt` — `pyyaml==6.0.2` (pin exacto). Primera línea no-stdlib en `hooks/_lib/`; justificada en kickoff (no hay parser YAML en stdlib; escribirlo a mano sería código muerto).
- Tests: `hooks/tests/test_lib_policy.py` nuevo (57 casos); tests de los 3 hooks actualizados (fixture escribe `policy.yaml` + autouse `_reset_policy_cache`; `TestIsEnforcedUnit`/`TestExpectedTestPairUnit` eliminadas en D3 por redundantes con loader test; `TestPolicyConstants` eliminada en D5 por mismo motivo). Global: **462 passed + 1 skipped**.

**Contexto a leer**:

- `policy.yaml` L24-45 (`lifecycle.pre_pr.docs_sync_*`), L80-120 (`lifecycle.post_merge.skills_conditional[0]`) + el nuevo bloque `pre_write.enforced_patterns`.
- `hooks/pre-write-guard.py`, `hooks/pre-pr-gate.py`, `hooks/post-action.py` pre-migración (referencia del hardcode que se elimina) + post-migración (consumo del loader).
- `.claude/rules/hooks.md § Tercer/Cuarto/Quinto hook` — documentación del hardcode que se reemplaza.
- `docs/ARCHITECTURE.md § 7` — Capa 1 (Hooks); el loader se integra aquí.

**Decisiones clave (Fase -1 aprobada)**:

- **Alternativa γ**: loader creado + migración completa de D3 + D4 + D5 en el mismo PR. Descartadas α (crear loader + que sólo D6 lo use; deja D3/D4/D5 con hardcode congelado — drift inmediato) y β (migrar sólo D4 o sólo D5; asimetría arbitraria).
- **(b.1) Strings/globs en YAML, derivación en Python keyed por `label`**. Descartado (b.2) YAML DSL (`derive: "replace_ext(.ts → .test.ts, co-locate)"`): abstracción prematura con una sola derivación real, endurecería el contrato antes de tiempo, difícil de testear aisladamente.
- **(c.2) Failure mode `None` + pass-through advisory `status: policy_unavailable`**. Descartado (c.1) deny defensivo (brickearía PRs ante un typo YAML — efecto bomba) y (c.3) fallback hardcoded a defaults (rompería el propósito de tener el loader como single-source-of-truth).
- **Slug `refactor/d5-policy-loader`, position "Rama D5b"**. Descartado insertarlo como Rama D6 propiamente dicha (D6 ya tiene scope propio: pre-compact + stop).
- **`pyyaml==6.0.2` pin exacto** (no `>=6.0,<7`). Razones: superficie pequeña, dependencia en módulo compartido — un upgrade semver-minor que cambie semántica de `yaml.safe_load` rompería todos los hooks silenciosamente; preferimos upgrade explícito.
- **Templates no se tocan en esta rama — drift temporal documentado**. Decisión explícita del usuario: *"No tocar `templates/policy.yaml.hbs` en esta rama me parece correcto, PERO: deja explícito en docs/plan/PR que existe un drift temporal meta-repo vs template — no quiero que nadie lea esta rama como 'el template ya refleja el nuevo shape'."* El drift se documenta en ROADMAP D5b, HANDOFF §11, ARCHITECTURE §7 y el propio cuerpo del PR. Rama reconciliadora (update template + renderer + snapshots + `pyyaml` en requirements-dev de proyectos Python generados) queda deferida a una rama propia post-D6.

**Contrato fijado por la suite**:

- `load_policy(None-dir)` → `None`. `load_policy(repo con policy.yaml corrupto)` → `None`. `load_policy(repo OK)` → dict parseado, cacheado.
- `docs_sync_rules(repo)` / `post_merge_trigger(repo)` / `pre_write_rules(repo)` cada uno devuelve `None` si el policy falta o la sección relevante está ausente. En happy path devuelven la dataclass tipada.
- `derive_test_pair("hooks/foo.py", "hooks_top_level_py")` → `"hooks/tests/test_foo.py"` (guiones → underscores). `derive_test_pair("generator/lib/bar.ts", "generator_ts")` → `"generator/lib/bar.test.ts"` (co-located, mismo dir).
- Los 3 hooks migrados: `policy_unavailable` logged + pass-through (no deny, no emisión de `additionalContext`) cuando el loader devuelve `None`.
- Cache invalidation: `reset_cache()` + mtime+size keying — segundo `load_policy()` tras `reset_cache` releer el file. Tests cubren este camino (ver `test_lib_policy.py::TestLoadPolicy::test_cache_invalidation`).

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Workaround fnmatch en `pre_write.enforced_patterns`**: `fnmatch.fnmatchcase("generator/run.ts", "generator/**/*.ts")` NO matchea — el middle `/` de `**` es literal, no recursivo. Solución: dos entries YAML con la misma `label: "generator_ts"` — una con `match_glob: "generator/*.ts"` (top-level), otra con `match_glob: "generator/**/*.ts"` (subdirs). El loader los carga como pattern-list y la derivación es label-driven, no pattern-driven. No aparecía en el plan original porque asumíamos `**` recursivo estilo git.
- **Divergencia D4 `hooks/tests/**` cerrada como side-effect**: al migrar D4 a consumir el loader, la forma natural de expresar la excepción es un campo `excludes` en la rule condicional. Se aplicó a `policy.yaml` en el mismo commit. La documentación D4 previa marcaba esto como "deferido a rama policy-loader" — cumplido.
- **Simplify pass pre-PR**: pendiente (paso 5 del sequence acordado "1. kickoff, 2. tests rojos, 3. implementación, 4. docs-sync, 5. simplify, 6. review").

**Drift documentado — meta-repo ↔ template** (reproducido en todas las docs y requerirá mención en el PR body):

- `policy.yaml` (meta-repo) ya con shape nuevo (`pre_write.enforced_patterns` + `excludes` en `hooks/**`).
- `templates/policy.yaml.hbs` + `generator/renderers/policy.ts` + snapshots `generator/__snapshots__/<profile>/policy.yaml.snap` **NO tocados** — siguen con el shape pre-D5b.
- Proyectos generados con `pos` hoy emiten un `policy.yaml` **desactualizado** respecto al del meta-repo. No es un bug del generador — es drift intencional para no saturar D5b.
- Rama reconciliadora: actualizar template + renderer + snapshots + añadir `pyyaml` al requirements-dev emitido para stacks Python. Diferida a post-D6.

**Criterio de salida**: 462 tests + 1 skipped verdes en `hooks/**`, coverage `_lib/policy.py` ≥95% (alcanzado 97%), D3/D4/D5 coverage sin regresión (93%/93%/94%), los 3 hooks consumen el loader sin residuos hardcoded, docs-sync en el propio PR (ROADMAP + HANDOFF + MASTER_PLAN + ARCHITECTURE + `.claude/rules/hooks.md`) incluyendo la nota drift meta↔template, hook `pre-pr-gate` aprueba este mismo PR (dogfooding D4 sobre D5b: los 5 docs obligatorios del loader están en el diff). En curso (paso 4 de 6 completado).

### Rama D6 — `feat/d6-hook-pre-compact-stop` — ✅

**Status**: cerrada en rama (PR pendiente). Última rama de Fase D antes de arrancar Fase E (skills). Entrega dos hooks en el mismo PR — cada uno encarna uno de los patrones canónicos ya vigentes en Capa 1.

**Scope entregado**:

- `hooks/pre-compact.py` — sexto hook, segunda aplicación del patrón **informative** (tras D2). Evento PreCompact; lee `lifecycle.pre_compact.persist` vía `pre_compact_rules()` y emite `hookSpecificOutput.additionalContext` con checklist de items a persistir antes de la truncación. Exit 0 siempre; nunca `permissionDecision`.
- `hooks/stop-policy-check.py` — séptimo hook, shape **blocker-scaffold** sobre evento Stop. Lee `skills_allowed_list()` + `.claude/logs/skills.jsonl`. Enforcement DEFERRED en prod hoy (meta-repo no declara `skills_allowed`); toda invocación real degrada a `status: deferred` pass-through. La cadena de enforcement vive en código y está ejercida end-to-end por fixtures.
- `hooks/_lib/policy.py` (extensión) — dos accessors nuevos: `pre_compact_rules(repo_root) → PreCompactRules | None` (dataclass frozen con `persist`) y `skills_allowed_list(repo_root) → tuple[str, ...] | None | SkillsAllowedInvalid` (contrato **tri-estado**: `None` = sección absent → deferred; `SKILLS_ALLOWED_INVALID` sentinel = presente pero mal formada → misconfigured observable; `()` = declarada vacía → deny-all explícito; tupla poblada = enforcement live).
- Tests: `hooks/tests/test_pre_compact.py` (25), `hooks/tests/test_stop_policy_check.py` (55), extensión de `test_lib_policy.py` (+20). Global **575 passed + 1 skipped** en `hooks/**`.
- `policy.yaml` sin cambios — `lifecycle.pre_compact.persist` ya existía desde Fase A. `skills_allowed` deliberadamente NO se añade (activaría enforcement antes de que E1a provea el logger `skills.jsonl`).
- `.claude/settings.json` no modificado: ya referenciaba los dos hooks desde Fase A; D6 sólo materializa los binarios.

**Contexto a leer**:

- `policy.yaml` — `lifecycle.pre_compact.persist` + (ausencia de) `skills_allowed`.
- `hooks/_lib/policy.py` pre-D6 (referencia de dataclasses + `_safe_str_list` + `_lifecycle_section`).
- `hooks/session-start.py` (patrón informative canonical D2) + `hooks/pre-branch-gate.py` (blocker canonical D1).
- `.claude/rules/hooks.md § Policy loader` — contrato de consumidor (c.2 failure mode).
- `docs/ARCHITECTURE.md § 7` — tres variantes canónicas de safe-fail en Capa 1.

**Decisiones clave (Fase -1 aprobada)**:

- **A2 — PreCompact = informative**. Descartado A1 (blocker). Razón: `/compact` puede ser user-invoked y bloquearlo niega una operación explícita. El caso de uso (reminder al modelo para persistir state) se resuelve mejor con `additionalContext` prompt-engineering que con deny.
- **c.3 — Stop = scaffold con deferred como default**. Descartado c.1 (empty enforcement activable inmediato con `skills_allowed: []` hardcoded). Sin `skills_allowed` en `policy.yaml`, la allowlist vacía como default bloquearía cada Stop del meta-repo hasta que E1a lo declare — "empty enforcement" infringe regla #7 y además rompe flujo diario. `None` como default semántico deja enforcement off hasta que el campo exista; `()` explícito es deny-all consciente.
- **both-together** (vs D6a/D6b split). Razón: los dos hooks comparten loader (dos accessors nuevos), patrón de tests, y docs-sync. Splitear multiplicaría overhead sin aislamiento de riesgo real.
- **Framing anti-sobrerrepresentación de `stop-policy-check`**. El hook NO se presenta como enforcement útil en prod hoy — es scaffold activable. Kickoff commit, module docstring, docs y body del PR deben reiterarlo explícitamente. Los tests que ejercen deny-path existen para lock-down del contrato, no como guardias operativos.
- **Skill invocation source = `.claude/logs/skills.jsonl`**. Alineado con `policy.yaml.audit.required_logs`. Cuando E1a entregue el logger (la primera skill que escriba ahí será `/pos:kickoff`), Stop enforza end-to-end sin refactor de hook.
- **Contrato tri-estado de `skills_allowed_list`** (post-review). Absent (`None`), invalid (sentinel `SKILLS_ALLOWED_INVALID`) y declarada-vacía (`()`) son **tres estados distintos**, no dos. Razón: colapsar "ausente" y "mal formada" en `None` hace que un typo en la policy apague enforcement silenciosamente como si fuera deferred legítimo. El sentinel explícito obliga al consumidor a distinguir y emitir `status: policy_misconfigured` observable. Fijado por tests: `test_real_skills_allowed_is_none_today` (prod absent), `test_explicit_empty_distinct_from_missing` (deny-all vs absent), `test_three_states_are_all_distinct` y `test_invalid_sentinel_distinct_from_none` (loader unit).

**Contrato fijado por la suite — PreCompact informative**:

- `additionalContext` contiene los 3 persist items del meta-repo hoy (`decisions_in_flight`, `phase_minus_one_state`, `unsaved_pattern_candidates`) + palabra `persist` en el texto.
- `auto` y `manual` triggers producen output idéntico (sólo cambia el log).
- Failure mode c.2: policy missing / malformed / sin `pre_compact` → log `status: policy_unavailable` + `additionalContext` mínimo advisory señalando que la policy no está disponible. Nunca deny. El wording exacto del advisory **no es contrato** — la suite valida presencia + shape, no string literal.
- Safe-fail informative (excepción canónica D2): stdin vacío / JSON inválido / top-level no-dict / lista / escalar → exit 0 + `additionalContext` mínimo describiendo el error de payload + log `status: payload_error`. Nunca `permissionDecision`. Wording exacto **no es contrato** (idem).
- Double log: `pre-compact.jsonl` siempre; `phase-gates.jsonl` evento `pre_compact` **sólo en happy path** (no se cruza la puerta sin checklist emitido).

**Contrato fijado por la suite — Stop blocker-scaffold**:

- Safe-fail blocker canonical (D1/D3/D4): malformación (empty stdin, JSON inválido, top-level no-dict, `session_id` ausente / no-string / vacío) → deny exit 2 con reason explicando la malformación. El hook no puede dejar pasar lo que no puede validar ni scopiar.
- Cuatro caminos de decisión real (tri-estado del loader + live enforcement):
  1. `policy.yaml` missing/malformed → log `status: policy_unavailable`, pass-through exit 0 (cero stdout).
  2. `policy.yaml` OK sin `skills_allowed` → log `status: deferred`, pass-through exit 0. **Estado actual de prod**.
  3. `skills_allowed` presente pero mal formada (escalar, lista con no-strings, dict) → loader devuelve `SKILLS_ALLOWED_INVALID`; log `status: policy_misconfigured` con razón literal `"skills_allowed is present in policy.yaml but not a list of strings"`, pass-through exit 0. **Distinto de deferred** — un typo no apaga enforcement silenciosamente.
  4. `skills_allowed` declarado como lista válida → lee `.claude/logs/skills.jsonl`, `_extract_invoked_skills(root, session_id) → list[str]`, `_validate(invoked, allowed) → (decision, violations)`. Violación → deny exit 2 con primer violador en `decisionReason` + guía literal `"Add it to the allowlist or revert the invocation."`. Sin violaciones → allow exit 0.
- **Session scoping** (post-review): el extractor filtra `skills.jsonl` por `session_id` del payload Stop. Entradas sin `session_id`, con `session_id` no-string, o pertenecientes a sesiones anteriores → ignoradas. El log es append-only y se contamina entre sesiones; sin scope, una skill rogue de ayer bloquearía el Stop de hoy. Cubierto por `TestSessionScoping` (6 casos, incluye `test_many_sessions_mixed` con 5 sesiones en el mismo log).
- Stream-parse línea a línea (`with log.open("r") as f: for raw_line in f:`) — memoria acotada frente a un audit log que crece indefinidamente; no `read_text().splitlines()`.
- Double log **sólo en decisiones reales**: `stop-policy-check.jsonl` (`{ts, hook, session_id, decision, ...}`) + `phase-gates.jsonl` evento `stop` (con `session_id` + `decision`). Los status advisory (`deferred`, `policy_misconfigured`, `policy_unavailable`) quedan sólo en el hook log.
- Corrupt `skills.jsonl` (líneas no-JSON, entries sin `skill`, `skill` no-string, `session_id` mal tipado) → ignoradas silenciosamente. El hook es enforcer, no forense.
- `skills_allowed: []` + invocación en la sesión → deny (deny-all explícito es política válida). `skills_allowed: []` + cero invocaciones scopiadas → allow.

**Ajustes vs plan original**:

- **Scope mantiene los dos hooks** — el plan original era lacónico ("persist decisions + valida skill invocations"); Fase -1 resolvió 6 concerns no triviales (informative vs blocker para pre-compact, real persistability, contrato skills_allowed, failure mode, evitar empty enforcement, both vs split) que quedaron canonicalizados arriba.
- **`pre_compact_rules` y `skills_allowed_list` añadidos al loader** en el mismo PR. No hay mirror hardcoded; cualquier hook futuro que consuma secciones nuevas de `policy.yaml` debe añadir un accessor antes que reparsear (regla canonical post-D5b).
- **Simplify pass pre-PR** (preferencia persistente del usuario): ninguna simplification requerida en esta rama. Los hooks D6 usan el mismo shape de los 5 previos; no hay helpers privados triviales que inlinear ni duplicación entre pre-compact y stop (sus lógicas son ortogonales — checklist emission vs allowlist enforcement).

**Criterio de salida**: 575 tests verdes + 1 skip intencional en `hooks/**` (tras integrar review PR #18), coverage loader extendido sin regresión (`_lib/policy.py` ≥95%), los dos hooks consumen el loader vía accessors nuevos sin hardcode residual, docs-sync en el propio PR (ROADMAP + HANDOFF + MASTER_PLAN + ARCHITECTURE + `.claude/rules/hooks.md`), framing anti-sobrerrepresentación explícito en kickoff + body del PR + docstring del hook Stop, `pre-pr-gate` aprueba este mismo PR (dogfooding). Cumplido.

---

## FASE E1 — Skills orquestación

### Rama E1a — `feat/e1a-skill-kickoff-handoff`

**Scope**: `.claude/skills/project-kickoff/SKILL.md`, `.claude/skills/writing-handoff/SKILL.md`, `.claude/skills/_shared/log-invocation.sh`. Primitive oficial de Claude Code Skills (NO `skill.json`, NO prefijo `pos:`, NO campos inventados). Activa scaffold D6 poblando `policy.yaml.skills_allowed`.

**Decisiones Fase -1 (v2, post-corrección del primitive)**:

- **Primitive correction (vs v1)**: Fase -1 v1 propuso `skill.json` + frontmatter extendido (`context`, `model`, `agent`, `effort`, `hooks`, `user-invocable`). Rechazado. El primitive oficial es exclusivamente `.claude/skills/<slug>/SKILL.md` + frontmatter YAML minimal (`name`, `description`, `allowed-tools` opcional). Si futuros releases del SDK documentan nuevos campos, se citan con fuente antes de introducirlos.
- **Nombres sin namespace `pos:`** — `project-kickoff` y `writing-handoff`, kebab-case. El primitive oficial no soporta prefijos como los slash commands; usar `pos:kickoff` como `name` rompe el parser.
- **C1 logger inline via Bash call** (descartado C2 hook nuevo, C3 sin log). Razón: simplicidad + no reabrir Fase D. Framing **best-effort operacional**: si el modelo omite el step, se pierde traza, no se rompe nada.
- **`writing-handoff` = Edit directo scoped** (descartado diff-only). Condición: scope estricto `HANDOFF.md` §1 / §9 / §6b / gotchas §7 — NUNCA `MASTER_PLAN.md` / `ROADMAP.md` / `docs/**` (esos son docs-sync del PR, no de la skill).
- **`.claude/skills/_shared/`** (descartado `_lib/`). Evita confusión con `hooks/_lib/`.
- **Tests split**: frontmatter contract en `.claude/skills/tests/`, integración con `stop-policy-check.py` en `hooks/tests/`. `pytest.ini` root-level con `--import-mode=importlib` para que ambos dirs convivan sin colisión de package `tests`.
- **Description framed `"Use when …"`** — selección eligible, no trigger garantizado. No prometemos auto-activación perfecta.
- **Log shape minimal y estable** `{ts, skill, session_id, status}` — sin `args`, sin `duration_ms`. Extender requiere nueva rama + migración del extractor.
- **`skills_allowed` poblado en E1a** (descartado diferirlo a E1b). Razón: `project-kickoff` es la primera skill que escribe `.claude/logs/skills.jsonl`; si hay skill + logger + hook scaffold, activar el scaffold en la misma rama cierra el loop.

**Contexto a leer**:

- `.claude/rules/skills-map.md` — filas E1a Core (se renombran en este PR).
- `hooks/_lib/policy.py::skills_allowed_list` — contrato tri-estado (`None`/`SKILLS_ALLOWED_INVALID`/`()`/tupla).
- `hooks/stop-policy-check.py` + `hooks/tests/test_stop_policy_check.py` — enforcement que se activa al poblar `skills_allowed`.
- `docs/ARCHITECTURE.md § Capa 2 Skills` — shape general de skills en el plugin (se actualiza en este PR para alinear con el primitive oficial).

**Criterio de salida**: 610 passed + 1 skipped en la suite conjunta `hooks/tests` + `.claude/skills/tests` (575 D6 baseline + 35 netos E1a — 24 frontmatter + 11 log-contract). D6 regression intacta. `test_real_skills_allowed_populated_by_e1a` flippa el pinpoint anterior. Docs-sync dentro del PR (ROADMAP + HANDOFF + MASTER_PLAN + `.claude/rules/skills-map.md` renombrando filas + `docs/ARCHITECTURE.md § 5 Skills` alineado con el primitive oficial). `pre-pr-gate.py` aprueba este PR (dogfooding D4 sobre E1a).

### Rama E1b — `feat/e1b-skill-branch-plan-interview` — ✅

**Scope**: `.claude/skills/branch-plan/SKILL.md`, `.claude/skills/deep-interview/SKILL.md`. Completa el par de skills de orquestación Fase -1 que E1a dejó abierto. Hereda contrato primitive-minimal canonizado en E1a (NO `skill.json`, NO prefijo `pos:`, NO campos inventados). Extiende `policy.yaml.skills_allowed` 2 → 4.

**Decisiones Fase -1 (v1 aprobada directa; E1a ya corrigió el primitive — no hay v2)**:

- **Decisión A1.a `branch-plan` delegation** (descartado A1.b main-strict). Razón: Fase -1 arquitectónica puede requerir cross-file analysis no trivial (múltiples prior gotchas + `docs/ARCHITECTURE.md § Capa X` + subtree de `generator/` o `hooks/`); cargar todo en main contamina contexto mientras la skill está activa. Delegación **inline vía Agent tool** con `subagent_type ∈ {Plan, code-architect, Explore}` es el **fork-aproximado primitive-correct**: el subagent corre en fork real; la skill sólo recibe summary. Para ramas lightweight (scope obvio + ≤2 files), la skill salta delegation y emite los seis entregables directamente en main.
- **Decisión A1.c `deep-interview` main-strict** (descartado A1.a con subagent). Razón: el coste de una entrevista NO está en reading (body dice literal "do NOT read `docs/ARCHITECTURE.md` top-to-bottom"); está en el dialog del usuario. Un subagent intermediaría sin valor y rompería la interactividad socrática. Lectura deliberadamente minimal: `MASTER_PLAN § Rama` + `HANDOFF §9` + `git log -10`.
- **Decisión A5.a — fix `skills.md` drift en E1b** (descartado A5.b diferirlo a E1c). Razón: `.claude/rules/skills.md` antes de E1b declaraba frontmatter extendido (`user-invocable`, `disable-model-invocation`, `model`, `effort`, `context`, `agent`, `hooks`, `paths`) + prefijo `pos:` + "La skill no debe loguear por sí misma" — todo contradice el contrato E1a. Reconciliamos en la misma rama que entrega las skills cuyo body es el testigo del contrato real.
- **Framing ajustes explícitos**:
  - `branch-plan` — disclaim literal "no crea marker / no abre rama / no ejecuta Fase -1 auto / solo produce paquete para aprobación" en `Scope (strict)` + `Explicitly out of scope`.
  - `deep-interview` — disclaim literal "opt-in real / no insiste / resume y se detiene / no muta docs/memoria salvo ratificación del usuario" en `Framing` + `Failure modes` + `Explicitly out of scope`. Step "user gives one-word / empty answers for two consecutive clusters → assume disengagement" cierra el caso "usuario no quiere seguir pero no lo dice explícito".
- **No se tocan E1a artifacts** — `project-kickoff` y `writing-handoff` quedan intactos. E1b sólo extiende la allowlist + añade dos skills nuevas + fixes de rule file. Regresión E1a cubierta por tests parametrizados.
- **`E1A_SKILLS` → `E1_SKILLS_KNOWN`**: constante renombrada contract-bound al allowlist (no era-bound). Extender la allowlist en E2a/E2b actualizará esta constante, no creará una nueva.
- **Logging via `log-invocation.sh`** sin cambios — helper heredado de E1a. `branch-plan` logea step 7, `deep-interview` logea step 7 con `status ∈ {declined, partial, ok}` según camino recorrido.

**Contexto a leer**:

- `.claude/skills/project-kickoff/SKILL.md` + `.claude/skills/writing-handoff/SKILL.md` — shape canónico E1a; E1b hereda el mismo primitive exacto.
- `.claude/skills/_shared/log-invocation.sh` — helper de logging heredado; las dos skills nuevas lo reusan sin cambios.
- `.claude/rules/skills-map.md` § Shape canónico + filas `branch-plan` / `deep-interview` — contenido autoritativo del contrato; E1b canonicaliza las filas (sin prefijo `/pos:*`).
- `.claude/rules/skills.md` — rule file drifted pre-E1b; E1b lo reconcilia (decisión A5.a).
- `hooks/_lib/policy.py::skills_allowed_list` — contrato tri-estado intacto, sólo crece la tupla esperada.
- `hooks/tests/test_skills_log_contract.py` — suite que valida end-to-end el contrato logger ↔ Stop hook; E1b añade el caso `test_all_four_e1_skills_end_to_end`.
- `.claude/skills/tests/test_skill_frontmatter.py` — suite que valida el shape primitive; E1b extiende la parametrización.

**Criterio de salida**: 639 passed + 1 skipped en la suite conjunta `hooks/tests` + `.claude/skills/tests` (+29 vs baseline E1a de 610: 22 parametrizados via `E1_SKILLS_KNOWN` 2→4 + 3 branch-plan behavior + 3 deep-interview behavior + 1 log-contract integration). E1a regression intacta. `test_real_skills_allowed_populated_by_e1b` flippa el pinpoint de la tupla 2→4. `stop-policy-check.py` sigue en enforcement live sin cambio de código. Docs-sync dentro del PR (ROADMAP + HANDOFF §1/§9/§14 + MASTER_PLAN § Rama E1b + `.claude/rules/skills-map.md` canonicalizando `/pos:branch-plan` → `branch-plan` y `/pos:deep-interview` → `deep-interview` + `.claude/rules/skills.md` reconciliado con el contrato E1a). `pre-pr-gate.py` aprueba este PR (dogfooding D4 sobre E1b).

---

## FASE E2 — Skills calidad

### Rama E2a — `feat/e2a-skill-review-simplify`

**Scope**: `.claude/skills/pre-commit-review/SKILL.md`, `.claude/skills/simplify/SKILL.md`. Primer par del bloque calidad Fase E — closing the `simplify → pre-commit-review` canonical pre-PR order. Shape heredado íntegro de E1a + E1b: primitive-minimal (`name` / `description` / `allowed-tools`), sin `skill.json`, sin prefijo `pos:`, sin campos inventados; logging best-effort via `.claude/skills/_shared/log-invocation.sh`.

**Decisiones Fase -1 ratificadas** (aprobadas por el usuario antes de abrir la rama):

- **A1.b — `simplify` writer scoped al branch diff**. La skill edita `Edit` **sólo** archivos presentes en `git diff --name-only main...HEAD` (derivación determinista en step 1 del body); **no crea archivos nuevos** (si una reducción lo requeriría, emite nota — nunca `Write`); **no toca archivos fuera del diff**; **no cambia comportamiento**; **no busca bugs** (ese es trabajo de `pre-commit-review`); **no hace refactor mayor**. Cierra con reporte de dos partes: "qué simplificó" + "qué decidió no tocar" con razón por cada skip. Precedente de scope estricto escritor: `writing-handoff` (E1a); precedente de read-only: `branch-plan` / `deep-interview` (E1b). A1.b consciente del tradeoff (el usuario no ve diff para pre-approval, fiando de la disciplina declarada en el body + tests de behavior).
- **A2.c — `pre-commit-review` híbrido main + subagent**. El main thread prepara el context ligero (branch kickoff commit, scope, invariantes aplicables del `.claude/rules/*.md` cuyos `paths:` solapen con el diff); la skill delega **via Agent tool inline** con `subagent_type="code-reviewer"` pasando ese context + `git diff main...HEAD` completo + asks explícitos (bugs, logic errors, security, adherencia a scope de rama, adherencia a invariantes citados); el subagent corre en fork real y devuelve summary confidence-filtered; el main folds ese summary (dedup + file:line + severity order + veredicto de una línea `clean to PR | findings blocking | findings advisory only`) — **no paste-through**. Extiende el precedente de delegación inline de `branch-plan` (E1b, A1.a) al caso de review. Main-strict (A2.a) descartado por coste en contexto; Agent-delegation-puro (A2.b) descartado por perder el framing de invariantes repo-specific que el subagent no vería.
- **A3.a — rename `E1_SKILLS_KNOWN` → `ALLOWED_SKILLS`**. La constante de `.claude/skills/tests/test_skill_frontmatter.py` cruza un límite de fase (E2a ya no es E1); mantener `E1_*` envejece mal. `ALLOWED_SKILLS` es contract-bound al `policy.yaml.skills_allowed` **entero** (no era-bound); la próxima rama extiende la lista, no renombra. Un único rename atómico en esta rama + update de la mención en `.claude/rules/skills.md` línea 61.
- **A5 — hardcodear `code-reviewer` en el body de `pre-commit-review`, con disclaimer**. Descartada la opción helper runtime + capability resolution dinámica (A5.alt). Razón: el coste de un helper no está justificado con una sola skill consumidora (regla #7 CLAUDE.md: ≥2 repeticiones antes de abstraer). Disclaimer literal en el body apunta a `.claude/rules/skills.md § Fork / delegación` para contexto; fallback a `general-purpose` declarado si el runtime enum no expone `code-reviewer`. Si una segunda skill consumidora aparece (E2b `/pos:audit-plugin` podría ser candidata), reabrir la decisión en esa rama.

**Framing contractual del body** (lock-down via behavior tests):

- `pre-commit-review`: "does not rewrite code" + "does not apply fixes" + "does not replace `simplify`" + "not a substitute for it" — literal, testeado por `TestPreCommitReviewBehavior::test_body_disclaims_writing_and_replacement`. Output declarado: "prioritized findings", confidence-filtered, severity-bucketed. Delegation explícita: `code-reviewer` + `subagent_type` + `git diff main...HEAD` aparecen literal en el body (testeado por `test_delegates_to_code_reviewer` + `test_scope_is_branch_diff`).
- `simplify`: `git diff --name-only main...HEAD` + "does not create new files" + "outside the diff" + "does not find bugs" + "does not change behavior" + "no major refactor" aparecen literal en el body (lock-down via 4 tests en `TestSimplifyBehavior`). Targets declarados de reducción: redundancia / ruido (noise) / complejidad accidental / abstracción prematura — al menos 2 de esos 6 tokens deben aparecer (test `test_body_frames_reducer_not_bug_finder`). Reporte final obligatorio: "qué simplificó / what was simplified" + "qué decidió no tocar / what it chose not to touch".

**Canonical order entre ambas** (documentado en ambos bodies):

`simplify → pre-commit-review`. Reduce primero para que el review opere sobre el diff más ligero. Ambas skills disclaim literal que **no se sustituyen entre sí**: running `pre-commit-review` does not obviate `simplify`; running `simplify` does not obviate `pre-commit-review`. Precedente doc-side recogido en `.claude/rules/skills-map.md` § Calidad.

**Entregables**:

- `.claude/skills/pre-commit-review/SKILL.md` — skill delegadora a `code-reviewer` subagent sobre `git diff main...HEAD`. `allowed-tools`: `Read`, `Grep`, `Bash(git log:*)`, `Bash(git diff:*)`, `Bash(git status:*)`, `Bash(git merge-base:*)`, `Bash(.claude/skills/_shared/log-invocation.sh:*)`. Body secciones: Framing + Scope strict (MAY / MUST NOT) + Delegation hybrid (main → Agent-tool → fold) + Steps 1–6 (identify scope / prepare context / delegate / fold summary / STOP / log) + Failure modes + Explicitly out of scope. Nunca emite `Edit` / `Write`. Logea via helper compartido.
- `.claude/skills/simplify/SKILL.md` — skill reductora writer-scoped. `allowed-tools`: `Read`, `Grep`, **`Edit`** (diferencia con `pre-commit-review`), `Bash(git log:*)`, `Bash(git diff:*)`, `Bash(git status:*)`, `Bash(git merge-base:*)`, `Bash(.claude/skills/_shared/log-invocation.sh:*)`. Body secciones: Framing + Scope strict (writer-scoped) + What counts as simplification (redundancia / ruido / complejidad accidental / abstracción prematura) + Steps 1–6 (derive scope / read diff / classify apply-vs-skip / apply / report / log) + Failure modes + Explicitly out of scope. Todo `Edit` call: `file_path` debe estar en la lista derivada en step 1 — si no, reclassify as `skip (out of scope)`.
- `policy.yaml.skills_allowed` extendida 4 → 6: `[project-kickoff, writing-handoff, branch-plan, deep-interview, pre-commit-review, simplify]`. Comentario inline actualizado (`E1a scaffold → E1b 4 skills → E2a 6 skills`). `stop-policy-check.py` continúa en enforcement live, ahora con 6 skills aceptadas.
- Tests (extensión, no reescritura):
  - `.claude/skills/tests/test_skill_frontmatter.py` — constante `E1_SKILLS_KNOWN` renombrada a `ALLOWED_SKILLS` (contract-bound al allowlist entero, no era-bound) + extendida 4 → 6. Todos los tests parametrizados (11 por skill × 6 skills = 66 automáticos) cubren el contrato. Añadidas dos clases nuevas: `TestPreCommitReviewBehavior` (3 casos: `test_delegates_to_code_reviewer` + `test_scope_is_branch_diff` + `test_body_disclaims_writing_and_replacement`) + `TestSimplifyBehavior` (4 casos: `test_allowed_tools_includes_edit` + `test_scope_limited_to_branch_diff_no_new_files` + `test_body_frames_reducer_not_bug_finder` + `test_body_reports_what_simplified_and_what_skipped`).
  - `hooks/tests/test_lib_policy.py::test_real_skills_allowed_populated_by_e1b` renombrado a `_by_e2a`; tupla esperada crece a 6 entries.
  - `hooks/tests/test_skills_log_contract.py::test_all_four_e1_skills_end_to_end` renombrado a `test_all_six_e1_e2a_skills_end_to_end`; allowlist + loop cubren las 6 skills.

**Contrato fijado por la suite** (extiende E1a + E1b sin reabrir):

- Primitive frontmatter inmutable (`name` / `description` / `allowed-tools`). Precedentes E1a + E1b intactos.
- `pre-commit-review` **nunca** edita, **nunca** abre PR, **nunca** sustituye a `simplify`. Tests `TestPreCommitReviewBehavior::test_body_disclaims_writing_and_replacement` lock down los 4 tokens literales (`findings` + `does not rewrite` / `does not apply` + `simplify` + `does not replace` / `not a substitute`).
- `simplify` **nunca** crea archivos, **nunca** toca archivos fuera del diff, **nunca** cambia comportamiento, **nunca** busca bugs, **nunca** hace refactor mayor. Tests `TestSimplifyBehavior` × 4 lock down cada disclaim + el derivado determinista del scope (`git diff --name-only main...HEAD` literal en body).
- `ALLOWED_SKILLS = 6` entries enforce vivo. La ausencia del 7º / 8º / ... slot cuando se invoque una skill no listada seguirá produciendo deny exit 2 (contrato D6 intacto).
- Canonical order `simplify → pre-commit-review` documentada en ambos bodies. Ambas disclaim replacement mutuo.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Decisión A1.b vs A1.a writer-scoped strictness** — elegido A1.b (strict writer scope al diff) vs A1.a (read-only proponer diff + user aplica). Razón: el ciclo pre-PR ya es largo (simplify → review → docs-sync → PR); añadir un paso "simplify propone, usuario aprueba" aporta fricción no proporcional al valor. La disciplina se asegura via behavior tests (4 locks) + el reporte final "qué decidió no tocar" que hace explícito el criterio del LLM en cada pasada. Si el usuario detecta drift en la disciplina declarada, el remedy es una PR correctiva, no un cambio de patrón.
- **Decisión A2.c vs A2.a/A2.b hybrid delegation** — elegido A2.c (main prepara context + subagent analiza + main folds) vs A2.a (all main) o A2.b (all subagent). Razón A2.a descarte: cargar la full diff + invariantes + kickoff commit + `.claude/rules/*.md` relevantes en main contamina contexto mientras la skill está activa. Razón A2.b descarte: el subagent ignoraría los invariantes repo-specific que sólo el main conoce por haber leído `.claude/rules/`. Hybrid captura lo mejor: main hace el work ligero + framing; subagent hace el work pesado + analysis. Precedente directo: `branch-plan` (E1b) delegation pattern.
- **Decisión A3.a rename inmediato** (vs A3.b mantener `E1_SKILLS_KNOWN` + añadir `E2_SKILLS_KNOWN`): un rename atómico vs dos constantes coexistiendo. El nombre es contract-bound al allowlist entero, no a la era — partir en dos constantes propagaría el envejecimiento a cada fase futura. El rename lleva actualización coordinada de una mención en `.claude/rules/skills.md` línea 61 (ver docs-sync).
- **Decisión A5 hardcode subagent name** (vs helper runtime con capability resolution): hardcode `code-reviewer` + disclaimer + fallback a `general-purpose`. Razón: una sola skill consumidora hoy; abstracción prematura (regla #7 CLAUDE.md). Reabrir cuando una segunda skill necesite delegation a un subagent nombrado — posible candidato E2b (`audit-plugin` puede necesitar `code-architect` o `Explore`).
- **Framing ajustes explícitos** (aprobados en Fase -1):
  - `simplify` body carries literal "does not create new files" / "outside the diff" / "does not find bugs" / "does not change behavior" / "no major refactor" en `Scope (strict)` + `Explicitly out of scope`. El step 4 "Apply the `apply` items with `Edit`" lleva la regla dura: "Scope check every call: the `file_path` must match an entry from step 1. If it doesn't, do NOT edit — re-classify as `skip (out of scope)`".
  - `pre-commit-review` body carries literal "Rewrite code. The skill does not rewrite code — it produces findings and never edits files." / "Apply fixes. The skill does not apply fixes." / "does not replace `simplify` and is not a substitute for it" en `Scope (strict) § You MUST NOT`.
  - Disclaimer hardcoded subagent: "The string `code-reviewer` here reflects the Claude Code default shipped today. It is hardcoded with a disclaimer: default `subagent_type` names can vary between releases/environments. If the Agent tool's `subagent_type` enum at runtime does NOT include `code-reviewer`, fall back to `general-purpose` with a task prompt that names the same capability" + referencia a `.claude/rules/skills.md § Fork / delegación`.
- **YAML parse gotcha atrapado en GREEN** — `simplify` frontmatter descripción v1 contenía "Writer scoped: edits files..." → el `: ` activaba el parser YAML como mapping-separator y el frontmatter fallaba entero. Fix aplicado inmediato: `Writer-scoped — edits files...` (em-dash). Lección generalizable para futuras skills: evitar `palabra: palabra` dentro de descriptions; usar em-dash o reescribir.

**Criterio de salida**: **668 passed + 1 skipped** en la suite conjunta `hooks/tests` + `.claude/skills/tests` (+29 vs baseline E1b de 639: 22 parametrizados `ALLOWED_SKILLS` 4→6 + 3 pre-commit-review behavior + 4 simplify behavior + 1 log-contract integration actualizado + 1 `test_real_skills_allowed_populated_by_e2a` ajustado — el skip es el D5 intencional `TestIntegrationDiffUnavailable` por subprocess-no-cover). E1a + E1b + D1..D6 regression intacta. `stop-policy-check.py` sigue en enforcement live, ahora con 6 skills aceptadas — sin cambio de código en el hook. Docs-sync dentro del PR (ROADMAP § E2a + HANDOFF §1 + §9 + §15 nuevo + MASTER_PLAN § Rama E2a + `.claude/rules/skills-map.md` canonicalizando las 2 filas Calidad `/pos:pre-commit-review` → `pre-commit-review` y `/pos:simplify` → `simplify` + `.claude/rules/skills.md` rename `E1_SKILLS_KNOWN` → `ALLOWED_SKILLS` + nota E2a como primera skill consumidora de `code-reviewer` + segunda skill writer-scoped tras `writing-handoff`). `docs/ARCHITECTURE.md` **no** requerido (E2a no toca `generator/` ni `hooks/`). El hook `pre-pr-gate.py` aprueba este mismo PR (dogfooding D4 sobre E2a).

### Rama E2b — `feat/e2b-skill-compress-audit-plugin`

**Scope**: `skills/compress/` (read-only advisory), `skills/audit-plugin/` (read-only advisory gate). Ambas heredan primitive minimal de E1a/E1b/E2a (SKILL.md official). E2b entrega skills funcionales pero advisory-only — enforcement/hard blocker/audit logs diferidos a rama posterior.

**Decisiones Fase -1 ratificadas**:
- A1a: `/pos:compress` read-only (no writer-scoped).
- A2a: `/pos:audit-plugin` read-only advisory gate (no hard enforcement).
- A3a: `audit-plugin` main-strict (no delegation).
- A4a: GO/NO-GO/NEEDS_MORE_INFO decision tri-estado basado en SAFETY_POLICY.md levels.
- A5a: Disclaimer "E2b advisory-only; enforcement deferred" en ambos bodies.

**Ajustes vs plan original**: ninguno — Fase -1 aprobada y se adhirió estrictamente.

**Resultado**:
- Tests: 668 (E2a baseline) + 22 parametrizados (8 skills × 11 tests) + 4 behavior ligeros = ~694 total, 1 skip. Suite pasa sin regresión.
- `policy.yaml.skills_allowed` extendido 6 → 8 (compress, audit-plugin).
- Bodies cierran contract via test assertions (advisory keywords presentes).
- Logging best-effort via `_shared/log-invocation.sh` sin cambios.

---

## FASE E3 — Skills patrones + tests

### Rama E3a — `feat/e3a-skill-compound-pattern-audit` ✅ PR #23

**Scope**: `skills/compound/SKILL.md`, `skills/pattern-audit/SKILL.md`. Sistema de captura + auditoría de patrones reutilizables.

**Decisiones ratificadas**:
- **A1**: `compound` es writer-scoped strict (solo `.claude/patterns/`, no refactoring de código). ✅
- **A2**: `pattern-audit` es read-only advisory, main-strict (sin delegación en E3a). ✅  
- **A3**: `compound` delega a `code-architect` con fallback `general-purpose`. ✅

**Entregables**:
- `/pos:compound` — Extrae patrones post-merge via Agent-tool hybrid (preparación → delegación → escritura local a `.claude/patterns/`).
- `/pos:pattern-audit` — Audita patrón registry por drift/inconsistencia (análisis local, reporte sin mutación).
- Formato de patrón fijado: `# Pattern: <name>` con secciones `## Context/Signal/Rule/Examples/Last observed`.
- Allowlist extendida: `skills_allowed` 8→10 entries en `policy.yaml`.
- 10 behavior contract tests (6 compound + 5 pattern-audit) — all GREEN. Test added: compound fallback to general-purpose declared in allowed-tools.

**Criterio de salida**: PR #23 merged tras docs-sync (ROADMAP, HANDOFF, MASTER_PLAN, skills-map actualizadas).

### Rama E3b — `feat/e3b-skill-test-scaffold-audit-coverage` ✅ PR #24

**Scope**: `skills/test-scaffold/SKILL.md`, `skills/test-audit/SKILL.md`, `skills/coverage-explain/SKILL.md`. Tercer bloque de Fase E (calidad de tests). Tres skills primitive-minimal heredando contrato canonizado en E1a/E1b/E2a/E2b/E3a — sin reabrir el frontmatter.

**Decisiones Fase -1 ratificadas** (tras una iteración de recorte de scope):

- **A1**: las tres skills son **main-strict** (sin Agent delegation). Razón: ninguna requiere cross-file analysis pesado — la complejidad está en el static analysis local o en lectura puntual de archivos, no en cross-cutting reading. Precedente directo: `pattern-audit` (E3a) main-strict por la misma razón.
- **A2**: `test-scaffold` es **writer-scoped strict** — tercera skill writer-scoped del repo (tras `writing-handoff` E1a y `simplify` E2a). Edita **solo** el test pair file derivado del source file que el usuario provee; **no modifica source**, **no toca otros archivos**. STOP boundary explícito cuando la convención del repo es ambigua (proporción <80% / split). Sigue patrón de scope-check en cada `Write` call.
- **A3**: `test-audit` y `coverage-explain` son **read-only advisory** (precedente: `compress` y `audit-plugin` E2b, `pattern-audit` E3a). Declaran candidate signals / strategy; **no mutan** archivos.
- **A4**: **No execution de tests/coverage**. Las tres skills tienen prohibido invocar `pytest`, `vitest`, `jest`, `npm run test-coverage`, `pytest --cov`, etc. Razón: ejecución de tests requiere environment válido (deps instaladas, fixtures preparadas) y puede introducir side effects — la skill no puede garantizar ese estado. Coverage execution sería duplicado de CI; coverage-explain opera sobre reportes ya generados.
- **A5 wording lock**: `test-audit` declara "candidate signals" (no "detecta"); `coverage-explain` declara "lee y explica" / "declara strategy" (no "parsea"). Lock-down via behavior tests del body.
- **A6 allowed-tools conservadores**: cada skill recibe solo el subset mínimo necesario. `test-scaffold`: `Glob`, `Grep`, `Read`, `Write`, `Bash(find:*)`, `Bash(git grep:*)`, logger. `test-audit`: `Glob`, `Grep`, `Read`, `Bash(find:*)`, `Bash(git grep:*)`, `Bash(wc:*)`, logger (sin `Write`). `coverage-explain`: `Glob`, `Grep`, `Read`, `Bash(find:*)`, logger (sin `Write`, sin `git grep`).

**Entregables**:

- `.claude/skills/test-scaffold/SKILL.md` — writer-scoped strict. Step 1 detecta convención (Glob sobre tests existentes); step 2 cuenta proporción; step 3 decide (≥80% → proceed, ambiguo → STOP + propose); step 4 escribe skeleton language-aware (vitest/jest shape para TS/JS, pytest shape para Python); step 5 reporta + STOP si conflict; step 6 logger.
- `.claude/skills/test-audit/SKILL.md` — read-only advisory main-strict. Step 1 discover test files via Glob; step 2 analyze each (flaky risk via Grep para asserts en loops/conditionals; orphan via import-path verification; trivial via `assert True/False/etc.` patterns); step 3 declare candidate signals con file:line + reasoning; step 4 report capped a 10 findings con severity tier (orphan ≥ flaky > trivial); step 5 disclaim de no-exhaustividad; step 6 logger.
- `.claude/skills/coverage-explain/SKILL.md` — read-only advisory main-strict. Step 1 locate report (lcov.json / coverage.json / htmlcov/ / .nyc_output / args path); step 2 parse con confidence-level disclaim; step 3 analyze gaps (red <50%, yellow 50–75%, green >75%); step 4 declare minimum target advisory (no mandatorio); step 5 report con table format; step 6 logger.
- `policy.yaml.skills_allowed` extendido 10 → 13: `[..., test-scaffold, test-audit, coverage-explain]`. Comentario inline actualizado (`E3a 10 skills → E3b 13 skills`).
- Tests behavior contract: `.claude/skills/tests/test_e3b_behavior.py` con 15 casos en 3 clases (`TestScaffoldBehavior` 5 + `TestAuditBehavior` 5 + `TestCoverageExplainBehavior` 5). Lock-down de los disclaim literales: writer-scoped, advisory-only, declares candidate, no execution, no mod, STOP boundary, types of signals (flaky/orphan/trivial), minimum targets framing.
- `.claude/skills/tests/_allowed_skills.py` — `ALLOWED_SKILLS` extendida 10 → 13 + header docstring actualizado con línea E3b.
- `hooks/tests/test_lib_policy.py::test_real_skills_allowed_populated_by_e3b` (rename desde `_by_e3a`) — tupla esperada crece 10 → 13.
- `hooks/tests/test_skills_log_contract.py::test_all_thirteen_e1_e3b_skills_end_to_end` (rename desde `_ten_e1_e3a_`) — emite una línea JSONL por cada una de las 13 skills, invoca Stop, asserta allow.

**Contrato fijado por la suite** (extiende E1..E3a sin reabrirlos):

- Primitive frontmatter inmutable (`name` / `description` / `allowed-tools`); sin `skill.json`; sin prefijo `pos:`; sin campos inventados. Precedentes E1a + E1b + E2a + E2b + E3a intactos.
- `test-scaffold` **nunca** modifica source code, **nunca** ejecuta tests, **nunca** modifica config/thresholds, **nunca** crea archivo si la convención es ambigua (STOP + propose).
- `test-audit` **nunca** ejecuta `pytest`/`vitest`/`jest`, **nunca** modifica archivos, **nunca** garantiza exhaustividad. Wording locked: "declares candidate signals" (los tests fallarían si el body usase "detects" sin `candidate`/`signal`/`declares`).
- `coverage-explain` **nunca** ejecuta `npm run test-coverage`/`pytest --cov`, **nunca** modifica `coverage.threshold`/`pyproject.toml`/`package.json`, **nunca** mandata un threshold (advisory, user decides).
- `ALLOWED_SKILLS = 13` entries enforce vivo. Invocar una skill no listada sigue produciendo deny exit 2 (contrato D6 intacto).

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Iteración de recorte (Fase -1 v1 → v2)**: la primera propuesta listaba `Bash(vitest:*)` y `Bash(pytest:*)` en allowed-tools de `test-audit`/`coverage-explain` y prometía "valid syntax/linting" como behavior test. Rechazado por el usuario: "hay que recortar scope para no prometer motores de análisis/generación que esta rama no implementa." V2 conservadora: cero ejecución, allowed-tools subset estricto, behavior tests verifican framing literal, no capabilities.
- **Wording correction post-V2**: "declares candidate signals" (no "detects"), "reads and explains coverage report data" / "declares missing coverage strategy" (no "parses coverage reports"). Aplicado en `description` + body.
- **YAML parse gotcha** (precedente E2a `simplify`): descripciones de `test-audit` y `coverage-explain` contenían colons dentro de paréntesis (`"declares candidate signals: flaky..."`) — el `: ` activaba YAML como mapping-separator. Fix: quote toda la description con `"..."`. Lección reforzada de E2a — generalizable: cuando una description tenga `palabra: palabra` sin comillas, fallará silently el frontmatter.

**Resultado**:

- Tests: ~720+ passed (baseline E3a + 22 parametrizados via `ALLOWED_SKILLS` 10→13 + 15 behavior contract + renames de 2 tests integration). Suite pasa sin regresión D1..D6 + E1a..E3a.
- `policy.yaml.skills_allowed` extendido 10 → 13.
- Bodies cierran contract via test assertions (writer-scoped, advisory keywords, no-execution disclaim).
- Logging best-effort via `_shared/log-invocation.sh` sin cambios.
- Docs-sync dentro del PR: `ROADMAP.md` (E3 ✅), `HANDOFF.md` (§1 + §9 actualizados + §17 Estado E3a + §18 Estado E3b nuevos), `MASTER_PLAN.md § Rama E3b` (esta sección expandida + cierre `✅ PR #24`), `.claude/rules/skills-map.md` (filas E3b finalizadas en sección Pattern + Test).

**Criterio de salida**: PR #24 merged tras CI verde post-docs-sync. Cierre de Fase E (todas las skills core entregadas); siguiente rama F1 (`feat/f1-skill-audit-session`).

---

## FASE F — Audit + release + marketplace

### Rama F1 — `feat/f1-skill-audit-session` ✅ PR pendiente

**Scope concreto**: `.claude/skills/audit-session/SKILL.md` — read-only advisory main-strict (precedente: `pattern-audit` E3a, `audit-plugin` E2b, `compress` E2b, `test-audit` + `coverage-explain` E3b). Compara **tres superficies explícitas** de `policy.yaml` contra el filesystem de `.claude/logs/`:

1. **Skills allowlist drift** — `policy.yaml.skills_allowed` (plain slugs) ↔ `.claude/logs/skills.jsonl` invocations distintas. Detecta `declared but never invoked` (allowlist entry muerto) y `invoked but not declared` (denegado hoy por Stop hook). Normaliza prefijo `pos:<slug>` ↔ `<slug>` antes de comparar.
2. **Lifecycle hooks/log drift** — `policy.yaml.lifecycle.<gate>.hooks_required` ↔ archivos `.claude/logs/<hook>.jsonl`. Detecta `declared hook with no log file`, `declared hook with empty log` (silently disabled) y `logging hook not declared in any lifecycle gate` (logueando huérfano).
3. **Required logs drift** — `policy.yaml.audit.required_logs` ↔ existencia + nonempty + mtime. Detecta archivos declarados ausentes / vacíos / antiguos (>30d advisory, sin block).

`policy.yaml.skills_allowed` extendido 13 → 14 (`audit-session`). Sin cambios en hooks (`stop-policy-check.py` ya enforce vivo desde D6 + E1a).

**Decisiones Fase -1 (ratificadas con 3 ajustes obligatorios del usuario)**:

- **A1.a — 3 surfaces explícitas (no exhaustive auditor)**. La skill es un "pattern-seeking advisor" sobre tres surfaces enumeradas, no un linter completo. Reabrir con segunda surface signal antes de añadir cuarta (regla #7 CLAUDE.md).
- **A2.a — review window default 30 days textual**. La guía es para el lector humano que interpreta el reporte; la skill **no ejecuta** date math ni filtra entries por timestamp. Cron / CI hook enforcement diferido (decisión A6.a).
- **A3.a — prefijo normalization explícito**. `policy.yaml.skills_allowed` lista plain slugs; `policy.yaml.lifecycle.*.skills_required` lista user-facing forms (`pos:` prefix). El body declara el supuesto de normalization antes de comparar. Decisión consciente, no bug.
- **A4.a — pre-existing drift `hooks.jsonl` reportado, no auto-fixed**. Hoy `audit.required_logs` declara `hooks.jsonl` pero los hooks logean a per-hook files (`pre-branch-gate.jsonl`, etc.). La skill reporta esto como Bucket 3 candidate; el usuario decide si actualizar `policy.yaml` o aceptar como aspiración documental. Que el finding emerja en la primera invocación es evidencia de que el advisor funciona.
- **A5.a — report estructurado por surface (3 sections + summary)**. Bullets `<entry> — <type>: <reasoning>`. Summary line con counts + disclaim advisory + review window + normalization assumption.
- **A6.a — `audit.session_audit.schedule` documental, no enforcement**. La cadencia (e.g. `weekly`) es declarativa en F1; cron / CI hook diferido a rama futura si signal emerge.

**Ajustes obligatorios del usuario (3) integrados durante Fase -1 → 1 → 2**:

- **Ajuste 1** — verificar shape real de `policy.yaml` antes de redactar el body (`hooks_required`, `required_logs` confirmados como claves canónicas).
- **Ajuste 2** — recortar `Bash(git log:*)` de allowed-tools (la skill no necesita git introspection). Final: `Glob`, `Grep`, `Read`, `Bash(find:*)`, `Bash(wc:*)`, `Bash(.claude/skills/_shared/log-invocation.sh:*)` — 6 entries.
- **Ajuste 3** — test del 30-day window valida **declaración** del body, no ejecución de date math. Reformulado a `assert "30" in body and ("day" in low or "review window" in low)`.

**Contexto a leer**:

- `MASTER_PLAN.md § Rama E3b` (precedente patrón read-only advisory main-strict + 3 skills entregadas).
- `.claude/rules/skills.md § Fork / delegación` (justifica main-strict).
- `.claude/skills/pattern-audit/SKILL.md` + `.claude/skills/test-audit/SKILL.md` (precedentes wording: `declares candidate signals`, no-execution disclaim).
- `policy.yaml § skills_allowed` (línea 282-295) + `policy.yaml § audit` (`required_logs`, `retention_days`, `session_audit.schedule`).
- `policy.yaml § lifecycle` (todas las `<gate>.hooks_required` keys).
- `.claude/logs/` filesystem real (`ls .claude/logs/`) para verificar pre-existing drift.

**Criterio de salida**: 793 verdes + 1 skip intencional. E1a..E3b + D1..D6 regression intacta. `test_real_skills_allowed_populated_by_f1` flippa la tupla 13→14. `stop-policy-check.py` sigue en enforcement live sin cambio de código. Docs-sync dentro del PR (ROADMAP § F1 detallado + Fase F abierta, HANDOFF §1+§9+§19, MASTER_PLAN § Rama F1 expandida con cierre `✅ PR pendiente`, `.claude/rules/skills-map.md` fila `audit-session` populada). `docs/ARCHITECTURE.md` **no** requerido (F1 no toca `generator/` ni `hooks/`). El hook `pre-pr-gate.py` aprueba este mismo PR (primer dogfooding D4 sobre Fase F).

**Carry-overs a F2..F4**:

- F2 (subagents): hoy `pre-commit-review` (E2a) y `compound` (E3a) referencian `subagent_type="code-reviewer"` y `code-architect` con disclaimer de fallback. F2 los entrega como contratos canónicos del plugin; evaluar `policy.yaml.agents_allowed` como nuevo top-level (precedente: `skills_allowed`).
- F3 (selftest): cuando `bin/pos-selftest.sh` exista, validar end-to-end que `audit-session` corre sobre el `policy.yaml` generado y reporta los 3 buckets correctamente.
- F4 (marketplace): `audit-session` entra en el set canónico de skills publicadas; sin cambios en su shape.

### Rama F2 — `feat/f2-agents-subagents`

**Scope**: 2 plugin subagent definitions con namespace `pos-*` en `agents/` — `pos-code-reviewer.md` (consumido por `pre-commit-review`, E2a) + `pos-architect.md` (consumido por `compound`, E3a). Cierra la asimetría heredada: hasta F1 las skills consumían defaults de Claude Code (`code-reviewer`, `code-architect`); F2 los entrega como contratos canónicos del plugin con namespace `pos-*` para evitar colisión y flippea las skills consumidoras.

**Archivos a crear/modificar**:

- `agents/pos-code-reviewer.md` (NEW) — frontmatter primitive-correct (`name` + `description` + `tools` comma-separated string + `model: sonnet`); body declara 5 capacidades (bugs, logic, security, scope, invariants); output contract findings agrupados por severidad. Hard limits explícitos.
- `agents/pos-architect.md` (NEW) — mismo shape; body declara 3 dimensiones (pattern extraction, architectural design, cross-file consistency); output contract pattern proposals canonical-format.
- `agents/tests/test_agent_frontmatter.py` (NEW) — 26 contract tests parametrizados por `ALLOWED_AGENTS = ["pos-code-reviewer", "pos-architect"]` (13 métodos × 2 slugs). 4 clases: structure, frontmatter, body, capability surfaces.
- `.claude/skills/pre-commit-review/SKILL.md` — flip `code-reviewer` → `pos-code-reviewer` (description + body + steps + failure modes). Fallback `general-purpose` literal intacto.
- `.claude/skills/compound/SKILL.md` — flip `code-architect` → `pos-architect`. Fallback `general-purpose` intacto.
- `.claude/skills/tests/test_skill_frontmatter.py` — `TestPreCommitReviewBehavior::test_delegates_to_pos_code_reviewer` + `TestCompoundBehavior::test_body_delegates_to_pos_architect_with_fallback` flippean nombres + asertan fallback. Negation lists de `pattern-audit` + `audit-session` extendidas con `pos-*` (forward-compat).

**Decisiones cerradas en Fase -1 (ratificadas por el usuario, v2 tras recorte de v1)**:

- (1) **Shape primitive** — oficial Claude Code subagent format: `name` + `description` + `tools` comma-separated string + `model: sonnet`; body Markdown como system prompt. **Shape distinto al skill primitive** (skill usa YAML list `allowed-tools`; agent usa string `tools`). Sin campos inventados; precedente E1a `feedback_skill_primitive_minimal.md` aplicado.
- (2) **Scope** — 2 agents, no 3. `auditor` diferido por falta de consumer real (regla #7 CLAUDE.md: ≥2 repeticiones documentadas antes de abstraer). Reabrir en rama dedicada si una skill futura lo requiere.
- (3) **Naming** — namespace `pos-*` obligatorio. Evita colisión con built-in defaults de Claude Code (`code-reviewer`, `code-architect`, `Plan`, `Explore`, `general-purpose`) y con user/project agents externos. NO override silencioso, NO nombres a secas.
- (4) **Policy** — `agents_allowed` NO añadido en F2. Sin enforcement consumer hoy (`stop-policy-check.py` lee `skills.jsonl`, no hay log de invocaciones de subagents). Sin tocar `policy.yaml`, `hooks/_lib/policy.py`, ni extender `audit-session`. Reabrir cuando un hook futuro requiera enforcement.
- (5) **Tests** — contract tests parametrizados por `ALLOWED_AGENTS` + behavior flips de skills consumidoras + forward-compat negation en main-strict skills.
- (6) **Docs-sync** — ROADMAP, HANDOFF (§1 + §8 + §9 + §20 nuevo), MASTER_PLAN § Rama F2 (este bloque), `.claude/rules/skills.md § Fork / delegación` (precedentes a plugin agents), `.claude/rules/skills-map.md` (sección "Subagents del plugin"), `docs/ARCHITECTURE.md § 6 Agents` (reescrita post-revisión PR — el nuevo top-level `agents/` es superficie arquitectónica del plugin, aunque el `pre-pr-gate` conditional no la exija para esta rama).

**Ajustes vs plan v1 (rechazado por el usuario)**:

- v1 listaba 3 agents (`code-reviewer`, `architect`, `auditor`) sin namespace + extensión de `policy.yaml.agents_allowed` + cambios en `hooks/_lib/policy.py`. **Rechazado**: scope a 2 agents (regla #7 sobre `auditor`), namespace `pos-*` obligatorio, no tocar `policy.yaml` ni hooks. v2 aprobado e implementado.
- **Hardcode literal con disclaimer** (precedente E2a A5): bodies hardcodean `pos-code-reviewer` / `pos-architect` con fallback `general-purpose`. Una sola consumidora por agent hoy → no justifica helper runtime (regla #7). Reabrir si segunda repetición.

**Contexto a leer**:

- `MASTER_PLAN.md § Rama F1` (precedente patrón Fase F open + read-only advisory).
- `.claude/rules/skills.md § Fork / delegación` (precedentes de hardcode + fallback).
- `.claude/rules/skills-map.md` (filas `pre-commit-review` E2a + `compound` E3a — consumers actuales).
- `.claude/skills/pre-commit-review/SKILL.md` + `.claude/skills/compound/SKILL.md` (bodies a flippear).
- `policy.yaml § skills_allowed` (líneas 263-296 — no se toca, pero confirmar para argumentar deferral de `agents_allowed`).
- `hooks/_lib/policy.py` (no se toca; confirmar superficie del loader para argumentar no-extensión).

**Criterio de salida**: **819 passed + 1 skipped** (baseline F1 793 + 26 netos del nuevo `agents/tests/test_agent_frontmatter.py` parametrizado [2 slugs × 13 métodos = 26 casos, incluyendo los 2 hardening añadidos en revisión PR: `tools`/`model` requeridos + `model == "sonnet"` lockeado]. Las behavior flips de `test_skill_frontmatter.py` actualizan assertions de tests existentes — sin delta de count.). E1a..F1 + D1..D6 regression intacta. `stop-policy-check.py` sigue en enforcement live con `ALLOWED_SKILLS = 14` (F2 no añade skills, solo agents). Docs-sync dentro del PR incluye `docs/ARCHITECTURE.md § 6 Agents` (reescrita post-revisión). El hook `pre-pr-gate.py` aprueba este mismo PR (segundo dogfooding D4 sobre Fase F).

**Carry-overs a F3..F4**:

- F3 (selftest): el smoke end-to-end puede dogfooding F2 invocando `pre-commit-review` y `compound` reales sobre el repo sintético; ejercita el resolution `pos-code-reviewer` / `pos-architect` con fallback `general-purpose` cuando el runtime sintético no expone agents del plugin.
- F4 (marketplace): los agents del plugin entran en el set canónico publicado; sin cambios en su shape.

### Rama F3 — `feat/f3-selftest-end-to-end`

**Scope**: `bin/pos-selftest.sh` + escenarios. Valida todos los gates con proyecto sintético.

### Rama F4 — `feat/f4-marketplace-public-repo`

**Scope**: crear repo `javiAI/pos-marketplace` con `marketplace.json` + release flow. Docs en `docs/RELEASE.md`.

---

## FASE G — Knowledge Plane (opcional)

> Capa opcional mountable dentro del repo generado (runtime plane), no en el meta-repo ni "sobre" el control-plane; su adopción se activa vía opt-in del questionnaire. Ver [docs/ARCHITECTURE.md § 1.1](docs/ARCHITECTURE.md) para encaje arquitectónico y terminología de tres capas (raw / wiki / schema).
>
> **Estado**: planificada, sin fecha de ejecución. Puede reordenarse o descartarse sin impacto sobre A..F.

### Rama G1 — `feat/g1-knowledge-plane-contract`

**Scope**: fijar el contrato tool-agnostic de la capa. Markdown file-based, tres capas separadas (raw / wiki / schema).

**Archivos (previstos)**:

- `docs/KNOWLEDGE_PLANE.md` — especificación conceptual (shape de `schema.md`, convenciones `raw/` y `wiki/`, invariantes).
- `.claude/rules/knowledge-plane.md` — rule path-scoped cuando se editan archivos bajo `vault/**`.
- `questionnaire/schema.yaml` — añade opt-in `integrations.knowledge_plane.enabled`. **Candidate shape to be finalized in G1**: no se decide en esta rama si el opt-in es bool único o sub-objeto `{ enabled, adapter, vault_path }`.

**NO incluye**: adapter concreto, renderer, ingest CLI, lint.

**Cuestión abierta** (a resolver en G1): el término `schema.md` colisiona léxicamente con `questionnaire/schema.yaml` (ya canonical). G1 decide renombre (p.ej. `vault/_meta.md`, `vault/config.md`) o justifica coexistencia.

**Contexto a leer**: [docs/ARCHITECTURE.md § 1.1](docs/ARCHITECTURE.md) (incluye link al gist de Karpathy sobre wikis LLM-friendly).

**Criterio de salida**: contrato público legible sin ambigüedad sobre qué es "raw" vs "wiki" vs "schema"; opt-in testeable; cero código de adapter o ingest.

### Rama G2 — `feat/g2-adapter-obsidian-reference`

**Scope**: **primer reference adapter** sobre Obsidian + Obsidian Web Clipper. Renderer nuevo que, cuando `integrations.knowledge_plane.enabled` está on, emite esqueleto mínimo del vault:

- `vault/schema.md` — template inicial (estructura, convenciones, cómo añadir fuentes).
- `vault/raw/.gitkeep`
- `vault/wiki/.gitkeep`

Documenta Obsidian Web Clipper como **ingestor manual recomendado** (extensión oficial que guarda páginas web como Markdown en el vault). **Adapter de referencia, no definitivo**: el knowledge plane permanece file-based/tool-agnostic — cualquier editor Markdown (Logseq, Foam, plain-text) es compatible por construcción.

**Archivos (previstos)**:

- `templates/vault/schema.md.hbs`
- `generator/renderers/knowledge-plane-obsidian.ts` + `*.test.ts` (co-located, patrón de C1–C5).
- `generator/renderers/index.ts` — registrar en nuevo grupo congelado `knowledgePlaneRenderers` (patrón `renderer-group` de [.claude/rules/generator.md](.claude/rules/generator.md)).
- `docs/ARCHITECTURE.md § 1.1` — ampliar con referencia al adapter entregado.

**NO incluye**: ingest automático, LLM calls, sync runtime, múltiples adapters.

**Criterio de salida**: con `integrations.knowledge_plane.enabled: true` en el profile, `npx tsx generator/run.ts --out <tmp>` emite `vault/` esqueleto; con flag off, no se emite nada. Tests semánticos sobre paths + contenido de `vault/schema.md`. Coverage ≥85% sobre el renderer nuevo.

### Rama G3 — `feat/g3-ingest-cli` (diferida)

**Scope**: stub CLI `pos knowledge ingest <path>`. Manual, sin LLM call, sin RAG. Copia/mueve un archivo a `vault/raw/` en posición canónica y emite un TODO en `vault/wiki/` para síntesis manual.

**Razón de diferimiento**: requiere G1 y G2 cerradas; sin contrato no hay comando sobre qué actuar.

### Rama G4 — `feat/g4-wiki-lint` (diferida)

**Scope**: skill `/pos:knowledge-lint` + hook opcional. Detecta links rotos en `vault/wiki/**`, orphan pages (raw sin sintetizar), wiki sin raw correspondiente, `schema.md` incoherente con el contenido emitido.

**Razón de diferimiento**: requiere ≥2 proyectos reales usando la capa para calibrar señales sin falsos positivos (CLAUDE.md regla #7).

---

## §3. Progreso por fase

Mantenido en [ROADMAP.md](ROADMAP.md). No duplicar estado aquí.

## §4. Reglas de refinamiento

- Si una rama descubre scope que no estaba en Fase -1 → parar, anotar en kickoff, pedir guía. No extender rama silenciosamente.
- Si un criterio de salida no se puede cumplir → volver a Fase -1 documentando el obstáculo real.
- Ramas se abren en orden salvo que dos no tengan dependencia (ej. C1..C5 parcialmente paralelizables — evaluado caso por caso).

## §5. Ramas bloqueadas / condicionales

Ninguna en la planificación inicial. Cualquier blockeo se documenta aquí con `**BLOCKED**: <razón>`.

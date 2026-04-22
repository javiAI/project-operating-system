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
- **Warning docs-sync** (decisión E1): se emite cuando `git diff --name-only main..HEAD` no incluye `ROADMAP.md` ni `HANDOFF.md`. Suprimido cuando la rama es `main`/`master` y cuando git no está disponible (evita falsos positivos en repos recién clonados o sin `main`).
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

### Rama D5 — `feat/d5-hook-post-action-compound`

**Scope**: `hooks/post-action.py` — detecta merge, lee `policy.yaml.lifecycle.post_merge.skills_conditional`, dispara `/pos:compound` si trigger match (touched_paths).

### Rama D6 — `feat/d6-hook-pre-compact-stop`

**Scope**: `hooks/pre-compact.py` (persist decisions) + `hooks/stop-policy-check.py` (valida skill invocations vs policy).

---

## FASE E1 — Skills orquestación

### Rama E1a — `feat/e1a-skill-kickoff-handoff`

**Scope**: `skills/kickoff/`, `skills/handoff-write/`. Ambas `context: main`, sonnet.

### Rama E1b — `feat/e1b-skill-branch-plan-interview`

**Scope**: `skills/branch-plan/`, `skills/deep-interview/`. Ambas `context: fork`, opus.

---

## FASE E2 — Skills calidad

### Rama E2a — `feat/e2a-skill-review-simplify`

**Scope**: `skills/pre-commit-review/`, `skills/simplify/`. Ambas `context: fork`, sonnet.

### Rama E2b — `feat/e2b-skill-compress-audit-plugin`

**Scope**: `skills/compress/` (haiku, fork), `skills/audit-plugin/` (sonnet, fork). Este último implementa `docs/SAFETY_POLICY.md`.

---

## FASE E3 — Skills patrones + tests

### Rama E3a — `feat/e3a-skill-compound-pattern-audit`

**Scope**: `skills/compound/`, `skills/pattern-audit/`. Implementan el sistema de captura de patrones.

### Rama E3b — `feat/e3b-skill-test-scaffold-audit-coverage`

**Scope**: `skills/test-scaffold/`, `skills/test-audit/`, `skills/coverage-explain/`.

---

## FASE F — Audit + release + marketplace

### Rama F1 — `feat/f1-skill-audit-session`

**Scope**: `skills/audit-session/` — compara policy.yaml vs logs.

### Rama F2 — `feat/f2-agents-subagents`

**Scope**: `agents/code-reviewer.md`, `agents/architect.md`, `agents/auditor.md` — subagent definitions.

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

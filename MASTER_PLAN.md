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

# ROADMAP — project-operating-system

Estado vivo. Cada fila refleja una rama de [MASTER_PLAN.md](MASTER_PLAN.md).

## Progreso general

| Fase | Descripción | Estado |
|---|---|---|
| A | Skeleton & bootstrap | ✅ |
| B | Cuestionario + profiles + runner | ✅ |
| C | Templates + renderers | 🔄 en curso (C1 ✅, C2 ✅, C3 ✅, C4 siguiente) |
| D | Hooks (Python) | ⏳ pendiente |
| E1 | Skills orquestación | ⏳ pendiente |
| E2 | Skills calidad | ⏳ pendiente |
| E3 | Skills patterns + tests | ⏳ pendiente |
| F | Audit + selftest + marketplace | ⏳ pendiente |

## Ramas

| Rama | Scope breve | Estado | PR |
|---|---|---|---|
| `feat/a-skeleton` | Bootstrap estructura + docs canónicos + policy | ✅ | — (commit inicial sin PR) |
| `feat/b1-questionnaire-schema` | Schema + questions YAML + validator | ✅ | #1 |
| `feat/b2-profiles-starter` | nextjs-app / agent-sdk / cli-tool | ✅ | #2 |
| `feat/b3-generator-runner` | `generator/run.ts` + validate-only runner (token-budget diferido) | ✅ | #3 |
| `feat/c1-renderers-core-docs` | CLAUDE/MASTER_PLAN/ROADMAP/HANDOFF/AGENTS/README renderers + pipeline + `--out`/`--dry-run` wire-up | ✅ | #4 |
| `feat/c2-renderers-policy-rules` | policy.yaml + rules path-scoped | ✅ | — |
| `feat/c3-renderers-tests-harness` | Test harness mínimo por stack | ✅ | — |
| `feat/c4-renderers-ci-cd` | GitHub/GitLab/Bitbucket workflows | ⏳ | — |
| `feat/c5-renderers-skills-hooks-copy` | Copia skills+hooks del plugin al proyecto destino | ⏳ | — |
| `feat/d1-hook-pre-branch-gate` | Bloqueo `git checkout -b` sin marker | ⏳ | — |
| `feat/d2-hook-session-start` | Snapshot 30s | ⏳ | — |
| `feat/d3-hook-pre-write-guard` | Test-pair + pattern injection + anti-pattern block | ⏳ | — |
| `feat/d4-hook-pre-pr-gate` | Policy vs logs + docs-sync + CI dry-run | ⏳ | — |
| `feat/d5-hook-post-action-compound` | Trigger `/pos:compound` por touched_paths | ⏳ | — |
| `feat/d6-hook-pre-compact-stop` | Persist pre-compact + stop policy check | ⏳ | — |
| `feat/e1a-skill-kickoff-handoff` | `/pos:kickoff`, `/pos:handoff-write` | ⏳ | — |
| `feat/e1b-skill-branch-plan-interview` | `/pos:branch-plan`, `/pos:deep-interview` | ⏳ | — |
| `feat/e2a-skill-review-simplify` | `/pos:pre-commit-review`, `/pos:simplify` | ⏳ | — |
| `feat/e2b-skill-compress-audit-plugin` | `/pos:compress`, `/pos:audit-plugin` | ⏳ | — |
| `feat/e3a-skill-compound-pattern-audit` | `/pos:compound`, `/pos:pattern-audit` | ⏳ | — |
| `feat/e3b-skill-test-scaffold-audit-coverage` | `/pos:test-scaffold`, `/pos:test-audit`, `/pos:coverage-explain` | ⏳ | — |
| `feat/f1-skill-audit-session` | `/pos:audit-session` | ⏳ | — |
| `feat/f2-agents-subagents` | 3 subagents | ⏳ | — |
| `feat/f3-selftest-end-to-end` | `bin/pos-selftest.sh` + escenarios | ⏳ | — |
| `feat/f4-marketplace-public-repo` | `javiAI/pos-marketplace` + release flow | ⏳ | — |

## Progreso Fase A

### `feat/a-skeleton` — bootstrap

Completada en la sesión inicial como excepción documentada (no hay sistema de aprobación hasta que esta misma rama lo crea).

Entregables:
- Estructura de directorios completa.
- `plugin.json`, `CLAUDE.md`, `policy.yaml` — canónicos.
- 7 rules path-scoped en `.claude/rules/`.
- Docs canónicos en raíz + `docs/`.
- `.claude/settings.local.json` con permisos + hooks stubs.
- `.gitignore`, `README.md`.

**Siguiente acción**: arrancar Fase -1 de `feat/b1-questionnaire-schema`.

## Progreso Fase B

### `feat/b1-questionnaire-schema` — ✅ PR #1

Entregables:

- `tools/lib/condition-parser.ts` — DSL mínimo (==, !=, in, &&, ||, !, paren, literales, paths).
- `tools/lib/meta-schema.ts` — zod schemas para `schema.yaml` + `questions.yaml`.
- `tools/lib/cross-validate.ts` — maps_to coverage, section coherence, enum option check.
- `tools/validate-questionnaire.ts` — CLI con exit 0/1/2 + `formatReport`.
- `tools/__fixtures__/` — valid / invalid-maps-to / bad-yaml.
- `questionnaire/schema.yaml` — 7 secciones A-G, 18 fields.
- `questionnaire/questions.yaml` — 22 questions con condicionales `when:`.
- `.github/workflows/ci.yml` — matrix ubuntu+macos, node 20, actions pineadas por SHA.
- `package.json`, `tsconfig.json`, `vitest.config.ts`, `.nvmrc`.

### `feat/b2-profiles-starter` — ✅ PR #2

Entregables:

- `questionnaire/profiles/{nextjs-app,agent-sdk,cli-tool}.yaml` — 3 profiles canónicos parciales.
- `tools/lib/profile-validator.ts` — parser ProfileFile + `validateProfile()` emitiendo 5 issue kinds.
- `tools/lib/read-yaml.ts` — shared YAML I/O (reuso desde `validate-profile` + `validate-questionnaire`, pattern-before-abstraction 2ª aplicación).
- `tools/validate-profile.ts` — CLI con exit 0/1/2 + `formatReport`.
- `tools/__fixtures__/profiles/valid/` — duplicados de los 3 canónicos.
- `tools/__fixtures__/profiles/invalid/` — 4 negativos (unknown-path, type-mismatch, enum-out-of-values, pattern-violation).
- `.github/workflows/ci.yml` — nuevo step `Validate profiles`.
- `package.json` — script `validate:profiles`.
- **Meta** (commit `chore(meta)`): sistematización Fase N+7 Context gate en CLAUDE/AGENTS/HANDOFF/rules.

**Brechas conocidas** (diferidas a rama posterior):

- `answer-value-not-in-array-allowlist` no se valida a nivel de instancia (ArrayField.values existe en schema).
- Campos `enum` con valor array/objeto emiten `answer-value-not-in-enum` en lugar de `answer-type-mismatch`.

### `feat/b3-generator-runner` — ✅ PR #3

Entregables:

- `generator/run.ts` — CLI entrypoint (`--profile`, `--validate-only`). `--out` y `--dry-run` rechazados con exit 2 + mensaje `flag --X not supported in B3; planned for C1`.
- `generator/lib/profile-loader.ts` — carga YAML reusando `tools/lib/read-yaml.ts`.
- `generator/lib/schema.ts` — re-exporta `parseSchemaFile` / `parseProfileFile` / `validateProfile` desde `tools/lib/` (3ª aplicación pattern-before-abstraction).
- `generator/lib/validators.ts` — `completenessCheck`: required-missing → error (exit 1); los 3 paths user-specific (`identity.name`/`description`/`owner`) warning-only (exit 0).
- `generator/__fixtures__/profiles/{valid-partial,missing-required,invalid-value}/` — fixtures integración CLI.
- Smoke CI `validate:generator` + step homónimo en `.github/workflows/ci.yml`.
- Tests unit + CLI (spawnSync). Coverage ≥85%.

**Ajuste vs plan original**: `generator/lib/token-budget.ts` diferido — `schema.yaml` no declara `workflow.token_budget` todavía, implementarlo sería abstracción prematura. Reintroducir cuando exista el campo.

## Progreso Fase C

### `feat/c1-renderers-core-docs` — ✅ (PR #4)

Entregables:

- 6 renderers puros en `generator/renderers/{claude-md,master-plan,roadmap,handoff,agents,readme}.ts`, cada uno `render(profile: Profile): FileWrite[]`. Frozen tuple `coreDocRenderers` en `generator/renderers/index.ts`.
- 6 templates Handlebars en `templates/{CLAUDE,MASTER_PLAN,ROADMAP,HANDOFF,AGENTS,README}.md.hbs`.
- `generator/lib/handlebars-helpers.ts` — `eq`, `neq`, `includes`, `kebabCase`, `upperFirst`, `jsonStringify`.
- `generator/lib/render-pipeline.ts` — `renderAll(profile, renderers)` falla explícitamente ante colisión de paths (invariante). `writeFiles(dir, files)` crea subdirs; `isDirEmpty(dir)` gate pre-escritura.
- `generator/lib/profile-model.ts` — `buildProfile(file)` expande dotted-answers a objeto nested, inyecta placeholders `TODO(identity.X)` para user-specific paths faltantes y emite `placeholders[]`.
- `generator/lib/template-loader.ts` — carga sincrónica desde `templates/` + registro de helpers (4ª aplicación pattern-before-abstraction).
- `generator/run.ts` — wire-up de `--out <dir>` y `--dry-run` + exports `runRender` / `formatRenderSummary`. Exit codes: `0|1|2|3`.
- 18 snapshots en `generator/__snapshots__/<slug>/*.md.snap` (3 profiles × 6 templates) vía `toMatchFileSnapshot`.
- Tests semánticos por renderer (paths + strings críticas) **además** de snapshots.
- Scripts `render:generator` + step CI homónimo en `.github/workflows/ci.yml`.
- Coverage global ≥85% (292 tests verdes).

**Ajuste vs plan original** (Fase -1): user-specific placeholders literales `TODO(identity.X)` con warning (no bloquea emisión); `docs.md.hbs` diferido a C2; `--out` con subdirs desde día 1; `FileWrite = { path, content }` sin `mode`; `render-pipeline` falla por invariante ante colisión; snapshots + tests semánticos coexisten; `--validate-only` conservado por compat; `--force` fuera de scope (dir no vacío → exit 3).

### `feat/c2-renderers-policy-rules` — ✅

Entregables:

- `generator/renderers/policy.ts` — renderer único para `policy.yaml` vía Handlebars template (`templates/policy.yaml.hbs`). Conditionals stack inline (`{{#if (eq answers.stack.language "typescript")}}`) para `pre_push.checks_required` y `testing.unit.framework_node|framework_python`. `type: "generated-project"` hard-coded; `project:` vía `{{answers.identity.name}}` (expande a `TODO(identity.name)` mientras los 3 paths user-specific no estén resueltos).
- `generator/renderers/rules.ts` — emite 2 archivos: `.claude/rules/docs.md` (cierra carry-over Fase N+7 de C1 con el bullet "Trazabilidad de contexto" referenciando `HANDOFF.md §3`) + `.claude/rules/patterns.md` (doctrina stack-agnóstica).
- `generator/renderers/index.ts` — nuevos exports `policyAndRulesRenderers` (2 renderers, frozen) y `allRenderers` (composición `[...coreDocRenderers, ...policyAndRulesRenderers]`, frozen). `coreDocRenderers` intacto.
- `generator/run.ts` — una sola línea cambiada: importa `allRenderers` en vez de `coreDocRenderers`. Estructura del runner sin más cambios (composición vive en `renderers/index.ts`, no en `run.ts`).
- `templates/policy.yaml.hbs`, `templates/.claude/rules/docs.md.hbs`, `templates/.claude/rules/patterns.md.hbs` — 3 templates Handlebars con decorative comments preservados.
- Tests unitarios: `policy.test.ts` (11 aserciones, `yaml.parse` OK, stack conditionals mutuamente exclusivos), `rules.test.ts` (6 aserciones, paths exactos + strings críticas), extensión de `index.test.ts` con `policyAndRulesRenderers` + `allRenderers` (9 paths únicos + determinismo).
- Snapshots: 27 (3 profiles × 9 templates) en `generator/__snapshots__/<slug>/*.snap` (se ampliaron los 18 de C1 con los 3 nuevos templates).
- `generator/run.test.ts` actualizado: 5 aserciones pasan de "6 files" a "9 files" + content checks para `type: "generated-project"` y "Trazabilidad de contexto".

**Ajustes vs plan original** (Fase -1 aprobada):

- Composición de renderers en `generator/renderers/index.ts`, **no** en `run.ts`. Estructura: `coreDocRenderers` + `policyAndRulesRenderers` + `allRenderers` (nuevo export). Evita que `run.ts` se convierta en sitio de composición creciente por fase.
- Scope de rules reducido a `docs.md` + `patterns.md` (no se incluyen `generator.md` / `templates.md` / `tests.md` / `ci-cd.md` / `skills-map.md`; quedan para una rama posterior cuando exista señal de necesidad stack-específica).
- `policy.yaml` emitido por un solo renderer con un solo template Handlebars (no se fragmenta por secciones). `type: "generated-project"` hardcoded en el template; `project:` usa `{{answers.identity.name}}` que expande a `TODO(identity.name)` vía `buildProfile`.
- Carry-over Fase N+7 completado: `templates/.claude/rules/docs.md.hbs` incluye el bullet de trazabilidad referenciando `HANDOFF.md §3`.

### `feat/c3-renderers-tests-harness` — ✅

Entregables:

- `generator/renderers/tests.ts` — renderer único que emite 4 archivos según combinación `stack.language` + `testing.unit_framework`: `typescript+vitest` → `tests/README.md` + `tests/smoke.test.ts` + `vitest.config.ts` + `Makefile`; `python+pytest` → `tests/README.md` + `tests/test_smoke.py` + `pytest.ini` + `Makefile`. Frameworks diferidos (`jest`, `go-test`, `cargo-test`) lanzan `Error` explícito con nombre del framework + "deferred" + referencia a `testing.unit_framework` desde dentro del renderer (no en `run.ts`).
- 6 templates Handlebars: `templates/Makefile.hbs` (universal, conditional TS vs Python, targets `test`/`test-unit`/`test-coverage`/`test-e2e`/`clean`), `templates/vitest.config.ts.hbs` (coverage thresholds parametrizados vía `{{answers.testing.coverage_threshold}}`), `templates/pytest.ini.hbs` (`--cov-fail-under=<threshold>` via `addopts`), `templates/tests/smoke.test.ts.hbs` + `templates/tests/test_smoke.py.hbs` (smoke real con assertion trivial), `templates/tests/README.md.hbs` (stack detection + entry-point + sección "Qué NO emite C3").
- `generator/renderers/index.ts` — nuevo export `testsHarnessRenderers` (frozen, 1 renderer). `allRenderers` recompuesto a `[...coreDocRenderers, ...policyAndRulesRenderers, ...testsHarnessRenderers]`. `run.ts` intacto.
- `generator/__fixtures__/profiles/valid-partial/profile.yaml` — añadidos `testing.coverage_threshold: 80` + `testing.e2e_framework: "none"` explícitos. Razón: `buildProfile` no materializa defaults del schema; los templates C3 referencian ambos paths. Defaults-in-profile queda diferido a rama posterior.
- Tests: `generator/renderers/tests.test.ts` (paths por profile canónico, strings críticas TS/Python, cross-stack verification [TS sin pytest, Python sin vitest], coverage threshold en configs, e2e sólo en README de `nextjs-app` [no emite `playwright.config.ts`], trailing `\n` en todos los FileWrite, determinismo byte-identical, 1 test por framework diferido asertando framework name + "deferred" + "testing.unit_framework"). `generator/renderers/index.test.ts` extendido con `testsHarnessRenderers` (length 1 + frozen) y `ALL_RENDERERS_EXPECTED_PATHS` per-profile (13 paths: 9 de C1/C2 + 4 de C3 variables por stack).
- Snapshots: +12 archivos en `generator/__snapshots__/<slug>/` (nextjs-app + cli-tool: `Makefile.snap` + `vitest.config.ts.snap` + `tests/README.md.snap` + `tests/smoke.test.ts.snap`; agent-sdk: `Makefile.snap` + `pytest.ini.snap` + `tests/README.md.snap` + `tests/test_smoke.py.snap`). Total: 27 (C1+C2) + 12 (C3) = 39.
- `generator/run.test.ts` actualizado: `runRender` returns 13 entries (was 9), dry-run header `/13 file\(s\) would be emitted/`, CLI integration `--out` writes top-level 11 entries + readFileSync checks para `Makefile` (`/^test:/m`), `vitest.config.ts` (`defineConfig`), `tests/smoke.test.ts` (`/describe\s*\(/`).

**Ajustes vs plan original** (Fase -1 aprobada):

- Scope reformulado como "test harness mínimo generado y estructuralmente coherente" — **no** emite `package.json` (TS) ni `pyproject.toml` (Python); la instalación real del stack es responsabilidad de una fase posterior. El README emitido documenta qué queda fuera del scope C3.
- Frameworks diferidos (`jest`, `go-test`, `cargo-test`) con fallo explícito y testeado dentro del renderer (no en `run.ts`): mensaje menciona el framework concreto, la palabra "deferred" y el path del schema (`testing.unit_framework`). Razón: CLAUDE.md regla #7 (patrones antes de abstraer) — ningún profile canónico los usa, 0 repeticiones documentadas.
- `testsHarnessRenderers` como grupo de **1 renderer único** (no fragmentado por archivo emitido), consistente con el patrón `policyAndRulesRenderers` (1 renderer que emite varios paths permitido si la condición stack gobierna el set completo).
- `Makefile` como entry-point universal (TS + Python); no se emite `package.json.scripts`. `vitest.config.ts` / `pytest.ini` mínimos pero válidos (incluyen coverage thresholds parametrizados desde el profile).
- `playwright.config.ts` **no** se emite (sólo mención en el README de `nextjs-app` cuando `testing.e2e_framework != "none"`). Razón: configuración e2e requiere paths de navegador/base-url/project setup que exceden un harness mínimo; se difiere a una fase posterior.
- `.claude/rules/tests.md` **no tocado** en C3 — el rule existente cubre ya la expectativa; expandirlo sin señal nueva sería ruido (guidance explícita Fase -1).

## Convenciones de este archivo

- Una fila por rama. `⏳` pendiente, `🔄` en vuelo, `✅` completada, `❌` abandonada, `🚫` bloqueada.
- Columna PR: `#N` o `—` si no aplica (commit directo, sólo para bootstrap de Fase A).
- Actualización: **dentro de la rama que cierra** (docs-sync Fase N+3). No post-merge.

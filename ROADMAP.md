# ROADMAP — project-operating-system

Estado vivo. Cada fila refleja una rama de [MASTER_PLAN.md](MASTER_PLAN.md).

## Progreso general

| Fase | Descripción | Estado |
|---|---|---|
| A | Skeleton & bootstrap | ✅ |
| B | Cuestionario + profiles + runner | ✅ |
| C | Templates + renderers | ✅ (C1 ✅, C2 ✅, C3 ✅, C4 ✅, C5 ✅) |
| D | Hooks (Python) | ⏳ parcial (D1 ✅, D2 ✅, D3 ✅) |
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
| `feat/c4-renderers-ci-cd` | GitHub Actions CI workflow + BRANCH_PROTECTION doc (GitLab/Bitbucket diferidos) | ✅ | — |
| `feat/c5-renderers-skills-hooks-copy` | `.claude/` skeleton (settings.json + hooks/README + skills/README); copia real diferida a D/E | ✅ | — |
| `feat/d1-hook-pre-branch-gate` | Bloqueo `git checkout -b` / `switch -c` / `worktree add -b` sin marker | ✅ | #11 |
| `feat/d2-hook-session-start` | Snapshot 30s + extracción `hooks/_lib/` (refactor D1) | ✅ | — (PR pendiente) |
| `feat/d3-hook-pre-write-guard` | Test-pair enforcement (PreToolUse(Write)); pattern injection + anti-pattern block diferidos post-E3a | ✅ | — (PR pendiente) |
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

### `feat/c4-renderers-ci-cd` — ✅

Entregables:

- `generator/renderers/ci-cd.ts` — renderer. Emite `.github/workflows/ci.yml` siempre (cuando `workflow.ci_host == "github"`); emite `docs/BRANCH_PROTECTION.md` sólo si `workflow.branch_protection == true`. `workflow.ci_host ∈ {gitlab, bitbucket}` → `Error` explícito con host + "deferred" + path del schema (mismo patrón que C3 con `jest`/`go-test`/`cargo-test`).
- 2 templates Handlebars: `templates/.github/workflows/ci.yml.hbs` (workflow estable `name: ci`, job único `unit`, stack-aware: TS→`setup-node` pinned + Node 20.17.0; Python→`setup-python` pinned + 3.11 + `pip install pytest pytest-cov`; invoca `make test-unit` y `make test-coverage` exclusivamente — nunca `npx vitest`/`pytest` directos; `${{ github.* }}` escapado con `\{{` para evitar interpretación de Handlebars); `templates/docs/BRANCH_PROTECTION.md.hbs` (doc dinámica listando job `unit` + targets Makefile invocados, consistente con el workflow).
- `generator/renderers/index.ts` — nuevo export `cicdRenderers` (frozen, 1 renderer). `allRenderers` recompuesto a `[...coreDocRenderers, ...policyAndRulesRenderers, ...testsHarnessRenderers, ...cicdRenderers]`. `run.ts` intacto (4ª aplicación del patrón `renderer-group`).
- `generator/__fixtures__/profiles/valid-partial/profile.yaml` — añadidos `workflow.ci_host: "github"` + `workflow.branch_protection: true` explícitos (mismo workaround que C3 por `buildProfile` sin materialización de defaults).
- Tests: `generator/renderers/ci-cd.test.ts` (paths por profile canónico, `yaml.parse(ci.yml)` OK, `name: ci` + `on.pull_request`/`push` estables, todas las `uses:` con SHA40 pin, job names estables `{unit}`, `make test-unit` Y `make test-coverage` aserciones independientes, prohibido `npx vitest`/`pytest` directos, stack conditionals sin leaks, consistencia cruzada `ci.yml` ↔ `BRANCH_PROTECTION.md`, `branch_protection=false` → sólo `ci.yml`, gitlab/bitbucket → Error con host + path + "deferred", trailing `\n`, determinismo byte-identical). `generator/renderers/index.test.ts` extendido con `cicdRenderers` (length 1 + frozen) y `ALL_RENDERERS_EXPECTED_PATHS` actualizado a 15 paths por profile.
- Snapshots: +6 (3 profiles × 2 archivos: `.github/workflows/ci.yml.snap` + `docs/BRANCH_PROTECTION.md.snap`). Total: 39 (C1+C2+C3) + 6 (C4) = 45.
- `generator/run.test.ts` actualizado: `runRender` returns 15 entries (was 13), dry-run header `/15 file\(s\) would be emitted/`, CLI integration `--out` writes top-level 13 entries (añade `.github` y `docs`) + readFileSync checks para `.github/workflows/ci.yml` (`/^name:\s*ci\s*$/m`), `docs/BRANCH_PROTECTION.md` (`/Branch Protection/`).

**Ajustes vs plan original** (Fase -1 aprobada):

- **Solo `ci.yml`** (A1). No `audit.yml` ni `release.yml` — quedan fuera de scope (release.yml depende de `workflow.release_strategy` con 3 ramas que divergen en pasos; rama propia posterior).
- **Runtime versions hardcoded** (A2): Node 20.17.0 (coincide con `.nvmrc` del meta-repo) + Python 3.11. Deuda documentada como rama futura en `.claude/rules/generator.md § Deferrals` (*schema: añadir `stack.runtime_version`*). Comentario breve en template, sin ensayos.
- **Coverage gate delegado al Makefile C3** (A3). El workflow solo invoca; no duplica lógica de thresholds.
- **`BRANCH_PROTECTION.md` dinámico** (A4): lista los jobs del `ci.yml` emitido, test de consistencia cruzada garantiza que ambos archivos se mantienen coherentes.
- **`gitlab` / `bitbucket` diferidos con `Error` explícito** (A5): mismo patrón que frameworks diferidos de C3. 0 repeticiones documentadas en profiles canónicos (CLAUDE.md #7). Reabrir cuando un profile canónico los adopte.
- **`branch_protection=false` → sólo `ci.yml`** (A6). No se emite `docs/BRANCH_PROTECTION.md` si el usuario desactiva la protección.
- **Python toolchain minimal** (no `uv`): `actions/setup-python` + `pip install pytest==8.3.4 pytest-cov==6.0.0`. Coherente con C3 que no emite `pyproject.toml`. Preferencia fuerte de toolchain (uv, poetry, pdm) se pospone hasta una rama que haga justificable la decisión desde el output actual del proyecto generado.
- **Contrato del workflow cerrado en revisión** (ajuste post-Fase-1 tras 2 pases de Copilot): ambas ramas declaran `Install test deps` con versiones pinneadas — TS: `npm install --no-save vitest@3.0.5 @vitest/coverage-v8@3.0.5` (alineado con `package.json` del meta-repo); Python: `pip install pytest==8.3.4 pytest-cov==6.0.0`. Tests semánticos en ambos stacks: presencia del step + versiones pinneadas + orden pre-`make test-unit`, más no-leak cruzado (TS sin `pip`/`pytest`; Python sin `npm`/`vitest`). Cuando C5/C6 emita `package.json`/`pyproject.toml`, migrar a `npm ci` / `pip install -e .[dev]` y sacar los pins al manifest.
- **Header comment de `BRANCH_PROTECTION.md.hbs`**: rebajado de "Dynamic: mirrors…" a guía alineada con el workflow + aviso explícito de que la lista de required checks se actualiza a mano (evita sugerir sincronización automática).
- **Branch protection no se aplica programáticamente**: documento markdown + aplicación manual en GitHub Settings. Mantiene la separación control-plane vs runtime-plane (ARCHITECTURE.md §1).

### `feat/c5-renderers-skills-hooks-copy` — ✅

Entregables:

- `generator/renderers/skills-hooks-skeleton.ts` — renderer único, 3 FileWrite por profile: `.claude/settings.json` + `.claude/hooks/README.md` + `.claude/skills/README.md`. Puro, byte-identical entre runs, stack-agnostic (sin menciones a vitest/pytest/npm/pip en el contenido emitido).
- 3 templates Handlebars: `templates/.claude/settings.json.hbs` (mínimo conservador: `hooks: {}` + `_note` explicando la deferral a Fase D; **no** siembra `permissions` baseline), `templates/.claude/hooks/README.md.hbs` (menciona `pos` + Fase D + palabra "diferid"), `templates/.claude/skills/README.md.hbs` (menciona `pos` + Fase E + "diferid").
- `generator/renderers/index.ts` — nuevo export `skillsHooksRenderers` (frozen, 1 renderer). `allRenderers` recompuesto a `[...coreDocRenderers, ...policyAndRulesRenderers, ...testsHarnessRenderers, ...cicdRenderers, ...skillsHooksRenderers]`. `run.ts` intacto (5ª aplicación del patrón `renderer-group` — ver historial en `.claude/rules/generator.md`).
- Tests: `generator/renderers/skills-hooks-skeleton.test.ts` (paths emitidos por los 3 canonicals, `JSON.parse(settings.json)` OK, `hooks === {}`, `_note` string >40 chars con `/pos/`, `permissions === undefined`, READMEs matching `/\bpos\b/` + `/Fase\s*D|E/` + `/diferid/i`, trailing `\n`, stack-agnostic, determinismo). `generator/renderers/index.test.ts` extendido con `skillsHooksRenderers` (length 1 + frozen) y `ALL_RENDERERS_EXPECTED_PATHS` actualizado a 18 paths por profile. `generator/run.test.ts` actualizado: `runRender` returns 18 entries (was 15), dry-run/write headers `/18 file\(s\)/`, CLI integration `--out` añade readFileSync checks de `.claude/settings.json` (JSON válido + `hooks: {}` + `_note` string) y de los READMEs (Fase D / Fase E).
- Snapshots: +9 (3 profiles × 3 archivos: `.claude/settings.json.snap` + `.claude/hooks/README.md.snap` + `.claude/skills/README.md.snap`). Total: 45 (C1+C2+C3+C4) + 9 (C5) = 54.
- Pipeline extremo a extremo: `validate:generator` exit 0 (3 canonicals, 3 warnings `identity.*` por diseño), `render:generator` dry-run emite 18 files/profile con los 3 nuevos paths presentes, `vitest run` 515/0.

**Ajustes vs plan original** (Fase -1 aprobada):

- **Scope recortado** — C5 **solo** cierra la estructura del directorio `.claude/`. **NO** implementa la copia real de hooks ejecutables ni de skills. Razón: los directorios `hooks/` y `skills/` de este repo no existen todavía; copiar placeholders o duplicar una instantánea en evolución activa sería abstracción prematura (CLAUDE.md regla #7). La copia real queda **diferida a rama post-D1/E1a**, cuando `pos` tenga un catálogo estable + canal de distribución firmado.
- **`FileWrite.mode` diferido** — el shape sigue siendo `{ path, content }` en C1–C5. La extensión a `{ path, content, mode? }` queda diferida a la primera rama que copie ejecutables reales (post-D1/E1a). C1–C4 no se rompen; snapshots previos no cambian.
- **`.claude/settings.json` mínimo conservador** — decisión explícita del usuario: solo `hooks: {}` + `_note`. **No** se siembra `permissions` baseline; esa decisión la toma Fase D cuando los hooks reales definan su superficie.
- **Renderer naming** — `skills-hooks-skeleton.ts` (no `settings-skeleton.ts`). Refleja el dominio real de la rama aunque el scope se haya recortado.
- **Docs-sync explícito** — esta entrada deja cristalino que C5 cierra la *estructura* de `.claude/`, no la *copia real*. El riesgo de ambigüedad fue la causa raíz del replanteo en Fase -1.

## Progreso Fase D

### `feat/d1-hook-pre-branch-gate` — ✅ PR #11

Entregables:

- `hooks/pre-branch-gate.py` (ejecutable, stdlib-only, Python 3.10+) — PreToolUse(Bash) hook que bloquea branch creation sin marker `.claude/branch-approvals/<sanitized-slug>.approved`. Detecta `git checkout -b`, `git switch -c`, `git worktree add -b` con `shlex.split` (robusto a quoting + global options pre-subcommand). `git branch <slug>` excluido (ref sin checkout ≠ inicio de trabajo).
- `hooks/tests/test_pre_branch_gate.py` — suite pytest (subprocess integration + in-process unit) cubriendo detection, pass-through, sanitization, logging, robustness, `sanitize_slug`, `extract_branch_slug`, `build_deny_reason`, `main()`. 99% coverage (única línea no cubierta: `sys.exit(main())` bajo `__main__` guard, intrínseco al script entrypoint).
- `hooks/tests/fixtures/payloads/` — 6 JSON fixtures (`checkout_b`, `switch_c`, `worktree_add_b`, `git_status`, `git_branch_no_flag`, `non_bash`).
- `requirements-dev.txt` — `pytest>=7`, `pytest-cov>=4`. Minimum viable test env, sin ruff ni infraestructura adicional.
- `.gitignore` — entradas Python (`/.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.coverage`).
- Double logging: `.claude/logs/pre-branch-gate.jsonl` (append-only) + `.claude/logs/phase-gates.jsonl` (evento `branch_creation`). Prepara `/pos:audit-session` (F3) sin refactor posterior.
- Mensaje al bloquear: ruta exacta del marker + comando `touch` sugerido + referencia textual a `MASTER_PLAN.md` (sin parseo). Pass-through silencioso en todo el resto.

**Ajustes vs plan original** (Fase -1 aprobada):

- **Alcance ampliado vs MASTER_PLAN.md L200**: además de `checkout -b` y `switch -c` (scope textual original), cubre `git worktree add -b` para tapar bypass obvio. `git branch <slug>` deliberadamente excluido.
- **Sin bypass env var** (`POS_SKIP_BRANCH_GATE=1` rechazado): el bypass legítimo es crear marker explícito.
- **Sin `hooks/_lib/` compartido**: CLAUDE.md regla #7 (≥2 repeticiones antes de abstraer). D1 es el primer hook; `sanitize_slug`/`append_jsonl`/`now_iso` quedan locales al archivo. Reevaluar extracción en D2 si se repiten.
- **Bootstrap de test env dentro de esta rama**: `.venv` local + `requirements-dev.txt`. Alternativa descartada: pip --user o `pyproject.toml` (ambas contaminan más o son ecosistema prematuro).
- **Sin `ruff`**: lint Python queda fuera de scope D1. Reabrir cuando exista justificación independiente.
- **Sin `bin/pos-selftest.sh`**: la integración end-to-end del plugin queda fuera de scope D1. La rama se limita a hook + test pair + docs-sync.
- **In-process tests añadidos vs Fase -1**: `pytest-cov` no mide subprocesses; se añadieron tests unitarios in-process (`importlib.util.spec_from_file_location` para cargar el módulo con guión en el nombre) para alcanzar el 85% comprometido. Subprocess tests conservados como integración end-to-end.
- **`.claude/settings.json` no modificado**: ya referencia `./hooks/pre-branch-gate.py` desde Fase A. D1 sólo materializa el binario ausente.

### `feat/d2-hook-session-start` — ✅ (PR pendiente)

Entregables:

- `hooks/session-start.py` (ejecutable, stdlib-only, Python 3.10+) — hook `SessionStart` que emite `hookSpecificOutput.additionalContext` con un snapshot ≤10 líneas (Branch / Phase / Last merge / Warnings). Exit 0 siempre; nunca emite `permissionDecision` (evento informativo). Mismo snapshot para `source ∈ {startup, resume, clear, compact}`.
- **`hooks/_lib/` extraído (2ª repetición tras D1, CLAUDE.md regla #7)**: `slug.py` (`sanitize_slug`), `jsonl.py` (`append_jsonl`), `time.py` (`now_iso`). `hooks/pre-branch-gate.py` refactorizado a importar desde `_lib` en el mismo PR (API pública intacta: `pbg.sanitize_slug` sigue funcionando vía re-export transitivo). Imports desde scripts ejecutables vía `sys.path.insert(0, str(Path(__file__).parent))` — sin convertir `hooks/` en paquete formal.
- `hooks/tests/test_session_start.py` (66 tests, 13 clases): `TestOutputEnvelope`, `TestSnapshotShape`, `TestPhaseDerivationFromBranch`, `TestPhaseDerivationFallbackOnMain`, `TestMarkerWarning`, `TestDocsSyncWarning`, `TestSourceInvariance`, `TestLogging`, `TestSafeFailGraceful`, `TestLastMerge`, `TestDerivePhaseFromSlugUnit`, `TestMainInProcess`. Subprocess integration + in-process (monkeypatched `chdir`/`stdin`) para cobertura visible de paths que corren `git` (pytest-cov no mide subprocess). Fixture `repo` con `git init -b main` aislado (`GIT_CONFIG_GLOBAL=/dev/null`, autor/fecha deterministas).
- 4 fixtures JSON nuevos: `session_startup.json` / `session_resume.json` / `session_clear.json` / `session_compact.json`.
- Double logging (patrón D1): `.claude/logs/session-start.jsonl` (shape `{ts, hook, source, branch, phase, warnings}`; en error path `{ts, hook, source?, error}`) + `.claude/logs/phase-gates.jsonl` (evento `session_start` con `{ts, event, source, branch, phase}`).

**Ajustes vs plan original** (Fase -1 aprobada):

- **Scope reformulado**: snapshot minimal <=10 líneas con orden fijo `Branch / Phase / Last merge / Warnings` y `"(none)"` literal cuando no hay warnings (ajuste explícito del usuario contra "menos automatismo ciego, más estructura + ayuda real"). Sin prose sobrante.
- **Phase derivation**: regex case-insensitive `^(feat|fix|chore|refactor)[/_]([a-z])(\d+)-` sobre el nombre de rama → letra+num.upper() (D2, C5, B12…). Fallback en `main`/`master` a `phase-gates.jsonl` mediante recorrido hacia adelante conservando la última fase parseable (streaming O(1) memoria, tolerante a JSONDecodeError por línea). Si nada resuelve → `"unknown"`. **No** parsea `MASTER_PLAN.md` ni `ROADMAP.md` (frágil).
- **Warnings activos**: `marker ausente` (rama no `main`/`master` sin `.claude/branch-approvals/<sanitize_slug(branch)>.approved`) + `docs-sync pendiente` (diff `main..HEAD` sin tocar `ROADMAP.md` ni `HANDOFF.md`). `docs-sync` es aviso-only; enforcement real queda diferido a D4 (`pre-pr-gate.py`). Warning "contexto >120k" descartado — no medible desde hook.
- **Safe-fail graceful canonizado** como excepción para hooks informativos (decisión G Fase -1): payload malformado → exit 0 + `additionalContext` con `(error reading payload: ...)` + log de error. Hooks bloqueantes (`PreToolUse`, `PreCompact`, `Stop`) mantienen `deny` + exit 2. Política canónica actualizada en `.claude/rules/hooks.md` y `docs/ARCHITECTURE.md §7`.
- **Extracción `_lib/` + refactor D1 en el mismo PR** (decisión A1): cierra deuda de duplicación antes de D3. Contenido mínimo (`sanitize_slug`, `append_jsonl`, `now_iso`); nuevos helpers sólo cuando ≥2 hooks los usen (regla #7).
- **Sin `hooks/tests/test_lib/`** (ajuste del usuario Fase -1): helpers triviales (3-20 líneas cada uno) cubren indirectamente desde los hook tests. Sobretestear `sanitize_slug("feat/x") == "feat_x"` en aislamiento sería ruido.
- **Subprocess git robusto** (decisión I Fase -1): `shell=False`, `cwd=Path.cwd()` explícito, `timeout=2s` por call, `check=False`. Maneja `FileNotFoundError` (git no instalado) y `SubprocessError`; cwd no-git → snapshot con branch=None, phase=unknown, sin crash.
- **`.claude/settings.json` no modificado**: ya referenciaba `./hooks/session-start.py` desde Fase A (wire existente con `timeout: 5s` + `statusMessage`). D2 sólo materializa el binario ausente (mismo patrón que D1).
- **Coverage**: 99% total en `hooks/**`. `hooks/session-start.py` 95% (6 líneas no cubiertas: FileNotFoundError/SubprocessError de git no instalado, 3 fallbacks de `_base_ref`/`_diff_touches_docs` cuando git falla, y `sys.exit(main())` del `__main__` guard). `hooks/pre-branch-gate.py` mantiene 99% tras refactor, sin regresión.

### `feat/d3-hook-pre-write-guard` — ✅ (PR pendiente)

Entregables:

- `hooks/pre-write-guard.py` (ejecutable, stdlib-only, Python 3.10+) — PreToolUse(Write) blocker que enforza CLAUDE.md regla #3 (test antes que implementación) sobre `hooks/*.py` top-level y `generator/**/*.ts`. Shape canónico blocker D1 (no patrón informative D2).
- Contrato fijado por la suite:
  - enforced + archivo inexistente + sin test pair → deny (exit 2).
  - enforced + archivo inexistente + con test pair → allow (exit 0).
  - enforced + archivo ya existente → allow (exit 0) — edit flow; D4 `pre-pr-gate` será el que detecte pérdida de cobertura sobre impl existente.
  - excluido o fuera de scope → pass-through silencioso (cero log).
- Clasificador con dos buckets de exclusión separados (tests/docs/templates/meta vs helper internals `hooks/_lib/**`); detalle completo en [.claude/rules/hooks.md § Tercer hook](.claude/rules/hooks.md).
- Expected test pair: `hooks/<name>.py` → `hooks/tests/test_<name_underscore>.py` (`-`→`_`); `generator/**/<name>.ts` → `<same-dir>/<name>.test.ts` (co-located, incluye `generator/run.ts`).
- Safe-fail blocker canonical (stdin vacío / JSON inválido / top-level o `tool_input` no-dict → deny exit 2). `file_path` ausente o no-string → pass-through exit 0 (decisión Fase -1).
- Double log: `.claude/logs/pre-write-guard.jsonl` + `.claude/logs/phase-gates.jsonl` (evento `pre_write`). Pass-throughs NO loguean (replica D1). Allow sobre impl existente sí loguea (trazabilidad del edit flow).
- Reuso `hooks/_lib/`: `append_jsonl` + `now_iso`. No introduce `read_jsonl` ni nuevos helpers.
- `.claude/settings.json` no modificado: wire existente desde Fase A con `timeout: 3`; D3 sólo materializa el binario.
- Tests: 81 casos en `hooks/tests/test_pre_write_guard.py`, 96% coverage. 219 totales en `hooks/**`; D1/D2 intactos.
- 6 fixtures JSON nuevos en `hooks/tests/fixtures/payloads/` con rutas relativas (normalizadas contra `Path.cwd()`).

**Ajustes vs plan original**: ver [MASTER_PLAN.md § Rama D3](MASTER_PLAN.md).

## Convenciones de este archivo

- Una fila por rama. `⏳` pendiente, `🔄` en vuelo, `✅` completada, `❌` abandonada, `🚫` bloqueada.
- Columna PR: `#N` o `—` si no aplica (commit directo, sólo para bootstrap de Fase A).
- Actualización: **dentro de la rama que cierra** (docs-sync Fase N+3). No post-merge.

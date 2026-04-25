# ROADMAP — project-operating-system

Estado vivo. Cada fila refleja una rama de [MASTER_PLAN.md](MASTER_PLAN.md).

## Progreso general

| Fase | Descripción | Estado |
|---|---|---|
| A | Skeleton & bootstrap | ✅ |
| B | Cuestionario + profiles + runner | ✅ |
| C | Templates + renderers | ✅ (C1 ✅, C2 ✅, C3 ✅, C4 ✅, C5 ✅) |
| D | Hooks (Python) | ✅ (D1..D6 + D5b) |
| E1 | Skills orquestación | ✅ (E1a + E1b) |
| E2 | Skills calidad | ✅ (E2a + E2b) |
| E3 | Skills patterns + tests | ✅ (E3a ✅, E3b ✅) |
| F | Audit + selftest + marketplace | ⏳ pendiente |
| G | Knowledge Plane (opcional) | ⏳ solo planificación (scope cerrado, sin implementación) |

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
| `feat/d4-hook-pre-pr-gate` | Docs-sync enforcer sobre `gh pr create` (shape D1 blocker); advisory scaffold skills/ci/invariants | ✅ | — (PR pendiente) |
| `feat/d5-hook-post-action-compound` | Trigger `/pos:compound` por touched_paths | ✅ | — (PR pendiente) |
| `refactor/d5-policy-loader` | Loader declarativo `hooks/_lib/policy.py` + migración D3/D4/D5 | ✅ | — (PR pendiente) |
| `feat/d6-hook-pre-compact-stop` | Sexto+séptimo hook (PreCompact informative + Stop blocker-scaffold) + loader accessors `pre_compact_rules`/`skills_allowed_list` | ✅ | — (PR pendiente) |
| `feat/e1a-skill-kickoff-handoff` | Skills `project-kickoff` + `writing-handoff` (primitive oficial Claude Code) + logger `_shared/log-invocation.sh` + `skills_allowed` activa scaffold D6 | ✅ | — (PR pendiente) |
| `feat/e1b-skill-branch-plan-interview` | Skills `branch-plan` (Fase -1 producer, Agent-tool delegation inline) + `deep-interview` (opt-in socratic, no silent mutation); `skills_allowed` a 4 entries | ✅ | — (PR pendiente) |
| `feat/e2a-skill-review-simplify` | Skills `pre-commit-review` (delegación a `code-reviewer` subagent sobre `git diff main...HEAD`) + `simplify` (writer scoped al branch diff; no crea archivos, no cambia comportamiento, no busca bugs); `skills_allowed` a 6 entries; rename `E1_SKILLS_KNOWN` → `ALLOWED_SKILLS` | ✅ | — (PR pendiente) |
| `feat/e2b-skill-compress-audit-plugin` | Read-only advisory skills: `/pos:compress` (context planner) + `/pos:audit-plugin` (community-tool gate); both E2b-scoped; enforcement deferred | ✅ | — (PR pendiente) |
| `feat/e3a-skill-compound-pattern-audit` | `/pos:compound` (writer-scoped pattern extraction, Agent delegation with fallback), `/pos:pattern-audit` (read-only advisory, main-strict analysis) | ✅ | #23 |
| `feat/e3b-skill-test-scaffold-audit-coverage` | `/pos:test-scaffold` (writer-scoped), `/pos:test-audit` (read-only advisory), `/pos:coverage-explain` (read-only advisory); `skills_allowed` 10→13 | ✅ | — (PR pendiente) |
| `feat/f1-skill-audit-session` | `/pos:audit-session` | ⏳ | — |
| `feat/f2-agents-subagents` | 3 subagents | ⏳ | — |
| `feat/f3-selftest-end-to-end` | `bin/pos-selftest.sh` + escenarios | ⏳ | — |
| `feat/f4-marketplace-public-repo` | `javiAI/pos-marketplace` + release flow | ⏳ | — |
| `feat/fx-knowledge-plane-plan` | Docs-only: abre FASE G en MASTER_PLAN (capa opcional knowledge plane) | ⏳ | — |
| `feat/g1-knowledge-plane-contract` | Contrato tool-agnostic (raw/wiki/schema) + opt-in questionnaire | ⏳ | — |
| `feat/g2-adapter-obsidian-reference` | Primer reference adapter: esqueleto `vault/` + Obsidian Web Clipper | ⏳ | — |
| `feat/g3-ingest-cli` | Stub CLI `pos knowledge ingest` (diferida) | ⏳ | — |
| `feat/g4-wiki-lint` | Skill `/pos:knowledge-lint` (diferida) | ⏳ | — |

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
- **Warnings activos**: `marker ausente` (rama no `main`/`master` sin `.claude/branch-approvals/<sanitize_slug(branch)>.approved`) + `docs-sync pendiente` (diff `main...HEAD` sin tocar `ROADMAP.md` ni `HANDOFF.md`). `docs-sync` es aviso-only; enforcement real queda diferido a D4 (`pre-pr-gate.py`). Warning "contexto >120k" descartado — no medible desde hook.
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
- Tests: 83 casos en `hooks/tests/test_pre_write_guard.py`, 95% coverage. 221 totales en `hooks/**`; D1/D2 intactos.
- 6 fixtures JSON nuevos en `hooks/tests/fixtures/payloads/` con rutas relativas (normalizadas contra `Path.cwd()`).

**Ajustes vs plan original**: ver [MASTER_PLAN.md § Rama D3](MASTER_PLAN.md).

### `feat/d4-hook-pre-pr-gate` — ✅ (PR pendiente)

Entregables:

- `hooks/pre-pr-gate.py` (ejecutable, stdlib-only, Python 3.10+) — PreToolUse(Bash) blocker que enforza CLAUDE.md regla #2 (docs dentro de la rama) sobre el trigger `gh pr create`. Shape canónico blocker D1 (tercera aplicación del patrón tras pre-branch-gate + pre-write-guard).
- Matcher: `shlex.split(command)` + `tokens[:3] == ["gh","pr","create"]`. Cubre flags `--draft`, `--title`, `--body`, `--base`. Todo lo demás (`gh pr list`/`view`/`edit`, `gh issue create`, `git push`, `git status`, non-Bash) → pass-through silencioso (cero log).
- Skip advisory con log explícito (NO silencioso): branch `main` / `master` / `HEAD` detached; cwd no es git repo; `git merge-base HEAD main` no resoluble (main borrada localmente). Las entradas van sólo al hook-log; `phase-gates.jsonl` intacto en skips.
- Empty diff (HEAD vs merge-base) → deny exit 2 con reason dedicado (`"PR creation blocked: no changes ... empty PR. Base: <sha>"`), textualmente separado del reason docs-sync para no inducir confusión al usuario.
- Docs-sync check (reglas hardcoded, mirror de `policy.yaml.lifecycle.pre_pr.docs_sync_required` + `docs_sync_conditional`):
  - **Required** (siempre): `ROADMAP.md` + `HANDOFF.md`.
  - **Conditional**: `generator/**` → `docs/ARCHITECTURE.md`; `hooks/**` (el hook excluye `hooks/tests/**` — divergencia deliberada vs `policy.yaml` que lista `hooks/**` uniforme; convergencia diferida a rama policy-loader) → `docs/ARCHITECTURE.md`; `skills/**` → `.claude/rules/skills-map.md`; `.claude/patterns/**` → `docs/ARCHITECTURE.md`.
  - Dedupe: `ARCHITECTURE.md` aparece una sola vez aunque múltiples prefijos lo exijan.
  - Triggering paths capeados a 3 por doc en el reason, con sufijo `... (+N more)` cuando hay más.
- Advisory scaffold no-blocking (activable sin cambio de shape): en cada decisión real (allow/deny) el hook emite 3 entradas `{status: "deferred", check: <name>}` al hook log — `skills_required`, `ci_dry_run_required`, `invariants_check`. NO se emiten en skip ni en pass-through. Se convertirán en enforcement real cuando sus ramas dedicadas aporten sustrato (Fase E* / CI dry-run propia / invariants directory poblado).
- Safe-fail blocker canonical D1: stdin vacío / JSON inválido / top-level no-dict / `tool_input` no-dict → deny exit 2. Command ausente / no-string / vacío / shlex unparsable → pass-through exit 0.
- Double log en decisiones reales (allow/deny/empty-diff):
  - `.claude/logs/pre-pr-gate.jsonl` — `{ts, hook, command, decision, reason}` + 3 entradas `deferred` advisory.
  - `.claude/logs/phase-gates.jsonl` — `{ts, event: "pre_pr", decision}`.
- Reuso `hooks/_lib/`: `append_jsonl` + `now_iso`. Sin nuevos helpers compartidos.
- `.claude/settings.json` no modificado: ya referenciaba `./hooks/pre-pr-gate.py` desde Fase A; D4 sólo materializa el binario.
- `diff_files()` devuelve `list[str] | None`: `None` = `git diff --name-only <base> HEAD` no disponible (subprocess falla) → skip advisory con `status: "skipped"` + reason `"git diff unavailable"`; `[]` = diff verdaderamente vacío → deny dedicado `empty PR`. Evita false-deny cuando `merge-base` resuelve pero el diff subprocess falla después.
- Tests: 101 casos en `hooks/tests/test_pre_pr_gate.py` (incluye `TestDiffUnavailable`: 5 casos para `diff_files() is None` vs `[]`), ≥94% coverage sobre `pre-pr-gate.py`. Suite global `hooks/**`: 322 passed (D1 + D2 + D3 + D4). Sin regresión.
- 3 fixtures JSON nuevos en `hooks/tests/fixtures/payloads/`: `gh_pr_create.json`, `gh_pr_create_draft.json`, `gh_pr_list.json`. Reuso de `git_status.json` + `non_bash.json` heredados de D1/D2.

**Ajustes vs plan original**: ver [MASTER_PLAN.md § Rama D4](MASTER_PLAN.md).

### `feat/d5-hook-post-action-compound` — ✅ (PR pendiente)

Entregables:

- `hooks/post-action.py` (ejecutable, stdlib-only, Python 3.10+) — PostToolUse(Bash) hook. **Primera aplicación del patrón PostToolUse non-blocking** (shape emparentado con el blocker D1 pero sin `permissionDecision` y con exit 0 siempre; referencia canonical para futuros PostToolUse hooks).
- **Detección jerárquica de 2 tiers** — Tier 1 (command match vía `shlex.split`): matcher A = `git merge <ref>` (excluye flags de control `--abort`/`--quit`/`--continue`/`--skip`); matcher C = `git pull` (excluye `--rebase`/`-r`). Tier 2 (confirmación post-hoc): `git reflog HEAD -1 --format=%gs` debe comenzar por `"merge "` (A) o `"pull:" | "pull "` y NO `"pull --rebase"` (C). Evita disparar en `git merge --abort` (Tier 1 descarta) o en pulls que terminan siendo rebase real sin flag explícito (Tier 2 descarta).
- **`gh pr merge` (matcher B) descartado del scope en Fase -1**: `tool_response.exit_code` no está garantizado por Claude Code en PostToolUse(Bash) y no hay forma confiable de distinguir éxito de fallo sin él. Reabrir cuando `gh` deje huella local observable (reflog/merged commit post-pull en el merge gate, p.ej.).
- Trigger match — literal mirror de `policy.yaml.lifecycle.post_merge.skills_conditional[0]`: `TRIGGER_GLOBS = [generator/lib/**, generator/renderers/**, hooks/**, skills/**, templates/**/*.hbs]`, `SKIP_IF_ONLY_GLOBS = [docs/**, *.md, .claude/patterns/**]`, `MIN_FILES_CHANGED = 2`. Derivación de paths tocados via `git diff --name-only HEAD@{1} HEAD`. Skip si `<2` paths o si todos caen en `SKIP_IF_ONLY_GLOBS`. Match con `fnmatch.fnmatch`.
- Contrato (exit 0 siempre):
  - Tier 1 no matchea → early return silencioso.
  - Tier 1 OK + Tier 2 no confirma → hook log `status: tier2_unconfirmed` (phase-gates intacto).
  - Tier 2 OK + diff no disponible → hook log `status: diff_unavailable` (phase-gates intacto).
  - Tier 2 OK + diff OK + no hay trigger match → hook log `status: confirmed_no_triggers` + phase-gates `post_merge`.
  - Tier 2 OK + diff OK + trigger match → hook log `status: confirmed_triggers_matched` + phase-gates `post_merge` + emite `hookSpecificOutput.additionalContext` con el prompt sugerido (`Consider running /pos:compound ...`).
- Advisory-only: el hook **nunca** dispatcha la skill `/pos:compound` (eso queda para E3a). En D5 sólo emite contexto sugerido; el usuario o el agente deciden correr la skill.
- `additionalContext` formato: 4 líneas — encabezado `D5 post_merge: compound triggers matched.`, `Matched trigger globs: <lista>`, `Touched: <cap 3 + "(+N more)">`, CTA `Consider running /pos:compound...`. Path display cap = 3 para no inundar contexto.
- Double log canonical (shape D1..D4): `.claude/logs/post-action.jsonl` (`{ts, hook, command, kind, status, ...}` — kind ∈ `git_merge`/`git_pull`) + `.claude/logs/phase-gates.jsonl` (evento `post_merge`, sólo en decisiones confirmadas). Pass-throughs (Tier 1 no matchea) NO loguean. Los dos status advisory (`tier2_unconfirmed`/`diff_unavailable`) **sólo loguean al hook log** — `phase-gates.jsonl` permanece intacto porque la puerta del lifecycle no se cruzó (no hubo merge/pull confirmado aún tocando paths observables).
- Safe-fail PostToolUse non-blocking: stdin vacío / JSON inválido / top-level no-dict / `tool_input` no-dict / `tool_name != "Bash"` / `command` ausente o vacío → early return 0 silencioso (no log). Bloquear un evento PostToolUse dejaría la acción ya ejecutada sin rastro útil; el patrón canónico es degradar a no-op.
- Subprocess git robusto (reusa patrón D2): `shell=False`, `cwd=Path.cwd()`, `timeout=5`, `check=False`, captura `FileNotFoundError` + `SubprocessError`; `None` en error — el caller degrada. Ningún camino sube excepción.
- Reuso `hooks/_lib/`: `append_jsonl` + `now_iso`. Sin nuevos helpers compartidos (regla #7: sólo añadir cuando ≥2 hooks lo reclamen; D1..D5 ya cumplen precondición para `append_jsonl`/`now_iso`, pero D5 no demanda nada nuevo).
- Hardcode literal de la política (segunda repetición tras D4): mirror directo de `policy.yaml.lifecycle.post_merge.skills_conditional` dentro del hook. **Regla #7 CLAUDE.md cumplida dos veces para el parser declarativo** — la rama policy-loader (post-D6) ahora tiene la señal crystal-clear para unificar D4 + D5 en un parser común.
- Tests: 111 casos en `hooks/tests/test_post_action.py` (17 clases — 6 in-process decoradas con `@needs_hook`, 11 subprocess integration), 110 pasados + 1 skipped intencional (`TestIntegrationDiffUnavailable` delega en `TestMainInProcess` vía `pytest.skip`). 97% coverage sobre `hooks/post-action.py` (líneas no cubiertas: subprocess error handling, extra>0 branch en `build_additional_context`, `__main__` guard). Suite global `hooks/**`: 432 passed, 1 skipped — D1+D2+D3+D4 intactos.
- 7 fixtures JSON nuevos en `hooks/tests/fixtures/payloads/`: `git_merge.json`, `git_merge_no_ff.json`, `git_merge_abort.json`, `git_pull.json`, `git_pull_rebase.json`, `gh_pr_merge.json` (negative — no matchea), `git_rebase.json` (negative — no matchea).
- Fixture topológica `repo_after_merge` (two-repo setup): upstream repo + local clone, commit divergente en upstream, `git pull` real sobre el local → reflog auténtico `"pull: ..."` + diff `HEAD@{1}..HEAD` auténtico para integration tests. Réplica `repo_after_merge_ff` (fast-forward) y `repo_after_pull` (non-ff merge).
- `.claude/settings.json` no modificado: ya referenciaba `./hooks/post-action.py` desde Fase A con `timeout: 5`; D5 sólo materializa el binario.
- **Simplify pass pre-PR** (preferencia persistente del usuario): helper privado `_match(path, glob)` eliminado e inlineado en `match_triggers` — era un wrapper trivial sobre `fnmatch.fnmatch` con un solo caller. Reduce 4 líneas sin perder legibilidad.

**Ajustes vs plan original**: ver [MASTER_PLAN.md § Rama D5](MASTER_PLAN.md).

### `refactor/d5-policy-loader` — ✅ (PR pendiente)

**Sub-rama D5b** — precondición (regla #7 CLAUDE.md cumplida dos veces por D4 + D5) ejecutada antes de arrancar D6. Cierra la deuda de duplicación hardcoded de `policy.yaml`
dentro de los hooks consumiendo un loader declarativo único. Mismo PR no tocar `templates/policy.yaml.hbs` — drift temporal meta-repo ↔ template documentado (ver más abajo).

Entregables:

- `hooks/_lib/policy.py` (stdlib + `pyyaml==6.0.2`) — loader tipado con `@dataclass(frozen=True)` para los 5 tipos consumidos por hooks: `ConditionalRule`, `DocsSyncRules`,
  `PostMergeTrigger`, `EnforcedPattern`, `PreWriteRules`. API pública: `load_policy(repo_root)` cached (clave = path abs únicamente — sin componente mtime/size, sin invalidación implícita por edits; `reset_cache()` para tests o para forzar recarga), tres
  accessors `docs_sync_rules(repo_root)` / `post_merge_trigger(repo_root)` / `pre_write_rules(repo_root)` (cada uno devuelve `None` si policy.yaml falta o la sección relevante
  no existe), y `derive_test_pair(rel_path, label)` con dos ramas (`hooks_top_level_py` + `generator_ts`) — la derivación queda **en código Python**, no en YAML, keyed por el
  campo `label` de cada `enforced_patterns` entry. Decisión (b.1) Fase -1: strings/globs declarativos, derivación procedural.
- `policy.yaml` — nuevo bloque `pre_write.enforced_patterns` con tres entries (labels: `hooks_top_level_py` + `generator_ts` × 2 — un entry para `generator/*.ts` top-level y otro
  para `generator/**/*.ts` recursivo, workaround por fnmatch no-recursivo en el middle `/`). Bloque `lifecycle.pre_pr.docs_sync_conditional` ajustado: `hooks/**` ahora con
  `excludes: ["hooks/tests/**"]` (convergencia hook↔policy; desaparece la "divergencia deliberada" documentada en D4).
- Migración de los tres hooks a consumir el loader:
  - `hooks/pre-write-guard.py` (D3) — `classify(rel_path, rules)` recorre `rules.enforced_patterns` con `fnmatch.fnmatchcase`; derivación del test pair vía
    `derive_test_pair(rel_path, label)`. Los dos buckets de exclusión (tests/docs/templates/meta vs `hooks/_lib/**`) siguen siendo pass-through silencioso — la lista de excluded
    no migra a YAML (sería abstracción prematura, la cubren los `exclude_globs` de cada pattern + el implicit fall-through del classifier).
  - `hooks/pre-pr-gate.py` (D4) — `check_docs_sync(files, rules)` y `_conditional_triggers(files, rules)` leen de `DocsSyncRules`. Advisory scaffold y todo el resto del shape
    D1-blocker intactos.
  - `hooks/post-action.py` (D5) — `match_triggers(paths, trigger)` lee de `PostMergeTrigger`. Tier 1/Tier 2 detection intacta; sólo cambia la fuente de los globs.
- Failure mode (c.2) Fase -1: `policy.yaml` ausente o corrupto → los tres accessors devuelven `None` y los hooks consumidores degradan a **pass-through advisory con
  `status: policy_unavailable` en el hook log**. Nunca deny blind (evita brick por un bad-YAML edit). Documentado como patrón canonical en `.claude/rules/hooks.md § Policy
  loader`.
- `requirements-dev.txt` — añadida línea `pyyaml==6.0.2` (pin exacto, acordado Fase -1). `_lib/policy.py` es el primer módulo no-stdlib en `hooks/_lib/`; justificación en
  kickoff + MASTER_PLAN.
- Tests: 57 casos nuevos en `hooks/tests/test_lib_policy.py` (loader cache behavior, los 3 accessors con happy path + missing section + missing file, derivación de test pairs
  por label, validación de fnmatch semantics). Tests de los 3 hooks actualizados: `test_pre_write_guard.py` (fixture escribe `policy.yaml` + autouse `_reset_policy_cache`;
  `TestIsEnforcedUnit` y `TestExpectedTestPairUnit` eliminadas — ~23 tests — redundantes con `test_lib_policy.py`), `test_pre_pr_gate.py` (helper `_test_rules()` inyecta
  `DocsSyncRules` en los 13 unit tests; fixture `repo` escribe `policy.yaml`), `test_post_action.py` (`_write_policy(root)` en 4 fixtures + 3 tests inline; `TestPolicyConstants`
  eliminada — 3 tests — sustituida por el loader test; 14 `TestMatchTriggers` reciben `_test_trigger()`). Resultado global: **462 passed + 1 skipped**, coverage `_lib/policy.py`
  97%, `pre-write-guard.py` 93%, `pre-pr-gate.py` 93%, `post-action.py` 94%.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Alternativa γ** (loader único consumido por los 3 hooks existentes), descartadas α (loader + solo D6 lo usa) y β (loader + migrar sólo D4 o sólo D5). Razón: la precondición
  regla #7 cumplida por D4+D5 habilita la migración completa; dejar hooks hardcoded tras crear el loader sería drift inmediato dentro del propio meta-repo.
- **Decisión (b.1)**: strings/globs en YAML; derivación de paths (`derive_test_pair`) en Python, keyed por `label`. Descartado YAML DSL (b.2) — sería abstracción prematura con
  una sola derivación real y endurecería el contrato antes de tiempo.
- **Decisión (c.2)**: failure mode degrada a pass-through advisory con `status: policy_unavailable`. Descartado (c.1) `deny` defensivo (bloquearía PRs ante un typo de YAML) y
  (c.3) fallback a defaults hardcoded (rompería el propósito de tener el loader como single-source-of-truth).
- **`templates/policy.yaml.hbs` NO tocado en esta rama — drift temporal meta-repo ↔ template**. El template que `pos` genera para proyectos nuevos **sigue con el shape previo a
  D5b**: sin `enforced_patterns` en la sección `pre_write`, y con `docs_sync_conditional.hooks/**` uniforme (sin `excludes: ["hooks/tests/**"]`). Consecuencia práctica: un
  proyecto generado hoy con `pos` emitirá un `policy.yaml` que **no** refleja el nuevo shape. La convergencia template ↔ meta-repo queda **diferida a una rama propia post-D6**
  que actualice el renderer `generator/renderers/policy.ts` y el template Handlebars en paralelo (además de añadir `pyyaml` al requirements-dev de proyectos Python generados).
  El README del PR debe reiterarlo: *esta rama NO indica que el template ya refleja el nuevo shape*.
- **Convergencia hook↔policy `hooks/tests/**`** cerrada dentro de esta rama: `policy.yaml.lifecycle.pre_pr.docs_sync_conditional.hooks/**` ahora incluye
  `excludes: ["hooks/tests/**"]`. La divergencia deliberada documentada en D4 desaparece — el loader + policy ya son fuente única coherente con la semántica del hook.
- **Workaround fnmatch**: `fnmatch.fnmatchcase("generator/run.ts", "generator/**/*.ts")` no matchea porque el middle `/` de `**` es literal en fnmatch. Solución: añadir un
  segundo `enforced_pattern` con `match_glob: "generator/*.ts"` (misma `label: "generator_ts"`). Dos entries YAML con la misma label son válidos — el loader los agrega y la
  derivación es label-driven, no pattern-driven.
- **Simplify pass pre-PR**: helper privado trivial eliminado (ver § Simplify pass a continuación).

**Drift temporal meta-repo ↔ template**: `templates/policy.yaml.hbs` está **intencionalmente desactualizado** respecto a `policy.yaml` del meta-repo. El shape nuevo de
`pre_write.enforced_patterns` y el `excludes: ["hooks/tests/**"]` en `docs_sync_conditional` viven **sólo en el meta-repo** tras esta rama. Reconciliar template + renderer +
requirements en una rama posterior.

**Simplify pass pre-PR**: TBD tras la auto-review — pendiente paso 5 del sequence acordado.

**Criterio de salida**: 462 tests verdes + 1 skipped en `hooks/**`, coverage `_lib/policy.py` ≥95% (alcanzado 97%), D3/D4/D5 coverage sin regresión (93%/93%/94%), los 3 hooks
consumen el loader sin residuos hardcoded, docs-sync en el propio PR (ROADMAP + HANDOFF + MASTER_PLAN + ARCHITECTURE + `.claude/rules/hooks.md`) incluyendo la nota de drift
meta↔template, hook `pre-pr-gate` aprueba este mismo PR (dogfooding post-migración). En curso.

### `feat/d6-hook-pre-compact-stop` — ✅ (PR pendiente)

**Rama final de Fase D** — cierra la entrega de hooks Python antes de arrancar Fase E (skills). Entrega dos hooks en el mismo PR (decisión Fase -1: `both-together` vs split), cada uno encarna uno de los patrones canónicos ya vigentes en Capa 1.

Entregables:

- `hooks/pre-compact.py` (ejecutable, stdlib + `_lib/`) — **sexto hook**, segunda aplicación del patrón **informative** tras D2. Evento PreCompact; lee `lifecycle.pre_compact.persist` vía `pre_compact_rules()` y emite `hookSpecificOutput.additionalContext` con la checklist de items a persistir antes de que `/compact` trunca la conversación. Exit 0 siempre; nunca `permissionDecision`. Bloquear un `/compact` invocado por el usuario sería destructivo — el caso de uso es prompt-engineering al modelo, no enforcement. Trigger `auto` vs `manual` registrado en el log pero sin efecto sobre la salida (mismo checklist en ambos).
- `hooks/stop-policy-check.py` (ejecutable, stdlib + `_lib/`) — **séptimo hook**, shape **blocker-scaffold** sobre evento Stop. Lee `skills_allowed_list()` + `.claude/logs/skills.jsonl`. Enforcement DEFERRED en producción hoy: `policy.yaml.skills_allowed` no existe todavía en el meta-repo, por lo que toda invocación real degrada a `status: deferred` pass-through. La cadena entera (extracción → validación → deny exit 2 con primer violador en `decisionReason`) vive en código y está ejercida end-to-end por fixtures que declaran `skills_allowed: [...]` explícito. Cuando E1a (o posterior) añada el campo a `policy.yaml`, enforcement se activa sin refactor.
- `hooks/_lib/policy.py` (extensión) — dos accessors nuevos keyed sobre secciones no cubiertas hasta hoy: `pre_compact_rules(repo_root) → PreCompactRules | None` (dataclass frozen con `persist: tuple[str, ...]`) y `skills_allowed_list(repo_root) → tuple[str, ...] | None`. Contrato diferenciado para `skills_allowed`: **`None` = campo absent (deferred — consumer pasa)**, **`()` = lista explícita vacía (deny-all — consumer enforza)**. Esta distinción es el núcleo del scaffold c.3 para el hook Stop.
- `hooks/_lib/policy.py` nuevo `PreCompactRules` dataclass frozen. Convenciones idénticas a las 5 dataclasses pre-existentes (regla #7 cumplida desde D5b).
- `policy.yaml` sin cambios estructurales — el campo `lifecycle.pre_compact.persist` ya existía desde Fase A; D6 le da consumidor. `skills_allowed` deliberadamente NO se añade (habilitaría enforcement antes de tiempo; el `skills.jsonl` logger vive en E1a).
- Tests: `hooks/tests/test_pre_compact.py` (25 casos — envelope, happy path, failure mode c.2, safe-fail informative, logging double, in-process coverage), `hooks/tests/test_stop_policy_check.py` (35 casos — envelope, deferred mode, activable enforcement vía fixture-written allowlist, safe-fail blocker canonical, logging, in-process coverage, unit tests del extractor y del validator). Extensión `hooks/tests/test_lib_policy.py` (17 casos nuevos: 9 `TestPreCompactRules` + 8 `TestSkillsAllowedList` + 2 `TestWrongShapeGuards` + real-repo pinpoint `test_real_pre_compact_rules` / `test_real_skills_allowed_is_none_today`). Nuevas fixtures: `pre_compact_auto.json`, `pre_compact_manual.json`, `stop.json`; extensión de `fixtures/policy/full.yaml` (bloque `lifecycle.pre_compact.persist` + `skills_allowed`). Global: **555 passed + 1 skipped** (+ 60 netos tras D5b — 25 pre-compact + 35 stop; test_lib_policy suma 17 sin regresión).
- `.claude/settings.json` no modificado: ya referenciaba `./hooks/pre-compact.py` y `./hooks/stop-policy-check.py` desde Fase A; D6 sólo materializa los binarios. Los warnings "hooks ausentes pero tolerados" en HANDOFF §7 desaparecen con esta rama.

Contrato fijado por la suite — PreCompact informative:

- `additionalContext` contiene los 3 persist items del meta-repo hoy (`decisions_in_flight`, `phase_minus_one_state`, `unsaved_pattern_candidates`).
- `auto` y `manual` producen output idéntico (trigger sólo en log).
- Failure mode c.2: policy missing / malformed / sin sección `pre_compact` → log `status: policy_unavailable` + `additionalContext` mínimo `pos pre-compact: policy unavailable (...)`. **Nunca deny blind**.
- Safe-fail informative: stdin vacío / JSON inválido / top-level no-dict / lista / escalar → exit 0 con `additionalContext` `"(error reading payload: ...)"` + log `status: payload_error`. Nunca `permissionDecision`, nunca exit 2 — misma excepción canónica documentada para SessionStart (D2) y ahora reforzada para PreCompact.
- Double log: `pre-compact.jsonl` siempre; `phase-gates.jsonl` evento `pre_compact` **sólo en happy path** (los caminos `policy_unavailable` y `payload_error` quedan sólo en el hook log — no cruzan la puerta del lifecycle sin checklist real emitido).

Contrato fijado por la suite — Stop blocker-scaffold:

- Safe-fail blocker canonical (D1/D3/D4): stdin vacío / JSON inválido / top-level no-dict → deny exit 2 con `permissionDecision: deny` + `decisionReason` explicando la malformación.
- Tres caminos de decisión real:
  1. `policy.yaml` ausente o corrupto → log `status: policy_unavailable`, pass-through exit 0 (zero stdout, no `permissionDecision`). Mismo shape que los otros hooks tras D5b.
  2. `policy.yaml` presente pero sin `skills_allowed` → log `status: deferred`, pass-through exit 0. **Estado actual del meta-repo en producción**.
  3. `skills_allowed` declarado → lee `.claude/logs/skills.jsonl` (canonical audit log declarado en `policy.yaml.audit.required_logs`), extrae nombres via `_extract_invoked_skills(repo_root)`, valida via `_validate(invoked, allowed) → (decision, violations)`. Violación → deny exit 2 con primer violador + guía literal (`"Add it to the allowlist or revert the invocation."`) en `decisionReason`. Sin violaciones → allow exit 0.
- Double log **sólo en decisiones reales**: `stop-policy-check.jsonl` (allow/deny con violations list) + `phase-gates.jsonl` evento `stop` (con `decision: allow|deny`). Los status advisory (`deferred`, `policy_unavailable`) quedan aislados en el hook log — la puerta del lifecycle no se cruza hasta que la enforcement está realmente activa.
- Corrupt `skills.jsonl` (líneas non-JSON, entries sin `skill`, `skill` no-string) → se ignoran silenciosamente; el hook no debe ser forense del log, sólo enforcer basado en lo que esté bien grabado.
- `skills_allowed: []` + cualquier invocación → deny (explicit deny-all es una política válida). `skills_allowed: []` + sin invocaciones → allow.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Decisión A2 (PreCompact = informative)**: descartado A1 (blocker). Razón: `/compact` puede ser user-invoked y bloquearlo equivale a negarle una operación explícita. El caso de uso (reminder al modelo para persistir state) se resuelve mejor con `additionalContext` prompt-engineering.
- **Decisión c.3 (Stop = scaffold con deferred como default)**: descartado c.1 (empty enforcement activable inmediato). `policy.yaml.skills_allowed` no existe; levantar el hook con `skills_allowed: []` hardcoded como default sería "empty enforcement" (infracción CLAUDE.md regla #7) y además bloquearía cada Stop del meta-repo hasta que E1a declare la allowlist. `None` como default semántico deja enforcement off hasta que el campo exista.
- **Decisión both-together**: descartado split en D6a + D6b. Razón: los dos hooks comparten el loader (dos accessors nuevos), el mismo patrón de tests (subprocess + in-process + unit), y el mismo docs-sync — splitear multiplicaría overhead sin aportar aislamiento de riesgo.
- **Framing anti-sobrerrepresentación**: `stop-policy-check.py` **no** se presenta como enforcement útil en producción hoy. Ni en el kickoff, ni en el module docstring, ni en esta entrada — el hook es **scaffold activable**, no enforcement vivo. Los tests que ejercen deny-path existen para lock-down del contrato, no para validar guardias operativos.
- **Skill invocation source = `.claude/logs/skills.jsonl`**. Elegido en Fase -1 por alinearse con `policy.yaml.audit.required_logs` (ya declarado). El logger que escribe ahí vive en E1a (skill `/pos:kickoff` será la primera); cuando llegue, Stop enforza end-to-end sin refactor.

**Criterio de salida**: 555 tests verdes + 1 skip intencional en `hooks/**` (sin regresión vs D5b: 462 + 60 nuevos D6 + 17 nuevos test_lib_policy + 16 re-correcciones menores en fixtures). Los dos hooks consumen el loader vía accessors nuevos, sin residuos hardcoded. Docs-sync en el propio PR (ROADMAP + HANDOFF + MASTER_PLAN + ARCHITECTURE + `.claude/rules/hooks.md`). El hook `pre-pr-gate` aprueba este mismo PR (dogfooding D4 sobre D6).

**Ajustes vs plan original**: ver [MASTER_PLAN.md § Rama D6](MASTER_PLAN.md).

## Progreso Fase E

### `feat/e1a-skill-kickoff-handoff` — ✅ (PR pendiente)

Primera rama de Fase E — **primera entrega de Claude Code Skills reales** del meta-repo. Cierra el scaffold D6: `skills_allowed` se puebla por primera vez en `policy.yaml`, lo que flip-flop el hook `stop-policy-check.py` de `status: deferred` pass-through a enforcement vivo sin tocar código.

Entregables:

- `.claude/skills/project-kickoff/SKILL.md` — skill 30s-snapshot. Lee `git log/status/rev-parse`, `ROADMAP.md` § ⏳ row, `HANDOFF.md` §1 + §9. Emite snapshot ≤12 líneas (branch, phase, last merge, next branch, warnings). **STOPS BEFORE Fase -1** — no crea markers, no ejecuta `branch-plan`. Logea via helper compartido (step 4, best-effort).
- `.claude/skills/writing-handoff/SKILL.md` — skill de cierre de rama. Edita **exclusivamente** `HANDOFF.md` §1, §9, §6b y gotchas §7; jamás toca `MASTER_PLAN.md` / `ROADMAP.md` / `docs/**` (gobernados por docs-sync del PR, no por la skill). Persiste decisiones durables a memoria proyectil (`project` type). Logea vía helper compartido (step 5).
- `.claude/skills/_shared/log-invocation.sh` — helper POSIX bash que emite **una línea JSONL** por invocación a `.claude/logs/skills.jsonl` con shape mínimo y estable `{ts, skill, session_id, status}`. Sin `args`, sin `duration_ms`. Fallback `session_id: "unknown"` si `CLAUDE_SESSION_ID` ausente; `mkdir -p` del directorio — crea si falta. **Best-effort operacional**: si el modelo omite el último paso de la skill, el sistema pierde traza de esa invocación pero nunca rompe. `stop-policy-check.py` trata ausencia de entrada como "no invocación" → allow (silencio ≠ violación).
- `policy.yaml` — añade `skills_allowed: [project-kickoff, writing-handoff]` a top-level (scope E1a). **Esto es el flip-switch** del D6 scaffold: una vez declarado, toda invocación logged para la sesión actual que NO esté en la lista deniega el Stop. El deny-path canonicaliza a `deny-all` cuando la lista es `[]` y `SKILLS_ALLOWED_INVALID` si la clave está mal formada (tri-estado declarado en `hooks/_lib/policy.py`).
- Tests:
  - `.claude/skills/tests/test_skill_frontmatter.py` — 24 casos (4 clases `TestStructure`, `TestFrontmatter`, `TestBody`, `TestSharedLogger`) parametrizados por slug. Valida: dir + SKILL.md existe; NO `skill.json`; frontmatter keys ⊆ `{name, description, allowed-tools}`; `name` == dir name; description case-insensitive `startswith "use when"`; `allowed-tools` es `list[str]` si presente; `name` sin prefijo `pos:`; body referencia `.claude/skills/_shared/log-invocation.sh`; shared logger existe y es ejecutable.
  - `hooks/tests/test_skills_log_contract.py` — 11 casos (3 clases `TestLoggerShape`, `TestExtractorReadsLoggerOutput`, `TestEnforcementEndToEnd`). Exercise end-to-end: logger emite exactamente 4 keys, append-only, default status=ok, crea logs dir si falta; `_extract_invoked_skills` lee output del logger; entradas de otra sesión ignoradas; enforcement real con nombres `project-kickoff` / `writing-handoff` (**este es el test que cruza la integración con D6**, usando los nombres reales — mientras `test_stop_policy_check.py` sigue usando placeholders `pos:*` como fixtures).
  - `hooks/tests/test_lib_policy.py::test_real_skills_allowed_populated_by_e1a` — antes asertaba `skills_allowed_list(repo_root) is None`. Renombrado y flippeado: ahora asserta `== ("project-kickoff", "writing-handoff")`. Lock-down del contrato entre `policy.yaml` y el accessor.
- `pytest.ini` (root-level) — `addopts = --import-mode=importlib`. Necesario para que pytest descubra tests en `hooks/tests/` y `.claude/skills/tests/` sin colisión de `__init__.py` (dos dirs `tests/` no-siblings → pytest intenta importar ambos como package `tests` y el segundo falla con `ModuleNotFoundError`). Importlib mode evita el shared prefix requirement.

Suite global post-E1a: **610 passed + 1 skipped** (575 D6 baseline + 11 log-contract + 24 frontmatter; el skip es el D5 intencional `TestIntegrationDiffUnavailable` por subprocess-no-cover). Sin regresión en `hooks/**`.

Contrato fijado por la suite:

- Skill primitive = `.claude/skills/<slug>/SKILL.md` con frontmatter YAML mínimo (`name`, `description`, `allowed-tools` opcional). **No `skill.json`**, **no prefijo `pos:`** en `name`, **no campos inventados** (`context`, `model`, `agent`, `effort`, `hooks`, `user-invocable` no existen en el primitive oficial; si alguna versión futura del SDK los añade, se citan con fuente antes de introducirlos).
- Description framed como `"Use when ..."` — selección eligible por el modelo, **no trigger garantizado**. El primitive de Claude Code ya canonicaliza así la auto-activación; no la prometemos como infalible.
- Log shape estable a 4 campos `{ts, skill, session_id, status}`. Extender requiere nueva rama + justificación + migración de `_extract_invoked_skills` + tests del contrato.
- `writing-handoff` **no** toca `MASTER_PLAN.md` / `ROADMAP.md` / `docs/**`. El PR en curso hace ese docs-sync; la skill escribe HANDOFF con scope estricto declarado en su body (§1, §9, §6b, gotchas). Si un futuro caller pide ampliar scope, abrir rama E1c — no extender E1a.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Primitive correction** — Fase -1 v1 propuso `skill.json` + frontmatter extendido (campos `context`, `model`, `agent`, `effort`). Rechazado por el usuario; reemitida v2 alineada con el primitive oficial de Claude Code (solo `SKILL.md` + YAML minimal). Aprendizaje permanente: si una primitive del SDK no tiene documentación oficial citable, no la inventamos por analogía con slash commands.
- **Decisión C1 (logger inline via Bash call)** — descartado C2 (hook nuevo) y C3 (sin log). Razón: C1 es suficiente para E1a y evita reabrir Fase D con un séptimo hook; el log es útil y el framing "best-effort operacional" lo sostiene sin prometer enforcement criptográfico.
- **Decisión `writing-handoff` = Edit directo (scoped)** — descartado diff-only. Razón: si la skill existe para escribir handoff, que escriba; diff-only introduce fricción artificial. Condición aceptada: scope estricto §1/§9/§6b/gotchas.
- **Decisión `_shared/` vs `_lib/`** — elegido `.claude/skills/_shared/`. Razón: no es librería runtime general, es utility compartida entre skills; `_lib/` se confundiría con `hooks/_lib/`.
- **Ubicación de tests** — split intencional: frontmatter en `.claude/skills/tests/` (dominio skills), integración log ↔ stop-policy-check en `hooks/tests/` (dominio consumer). Pytest `--import-mode=importlib` en raíz para que ambos dirs convivan.
- **`skills_allowed` poblado en esta rama** — descartado "E1a-sin-allowlist + E1b activa". Razón: la skill `project-kickoff` es la primera que escribe `.claude/logs/skills.jsonl`; si hay skill + hay logger + hay hook scaffold, activar el scaffold en la misma rama que lo habilita cierra el loop sin dejar scaffold dormido entre ramas.

**Criterio de salida**: 610 tests verdes + 1 skip intencional en todas las suites (`hooks/tests` + `.claude/skills/tests`). D6 regression intacto; `test_real_skills_allowed_populated_by_e1a` flippa el pinpoint anterior al estado esperado. Docs-sync dentro del PR (ROADMAP + HANDOFF + MASTER_PLAN + `docs/ARCHITECTURE.md` §5 Skills + `.claude/rules/skills-map.md` renombrando `/pos:kickoff` → `project-kickoff` y `/pos:handoff-write` → `writing-handoff` + AGENTS.md si procede). El hook `pre-pr-gate.py` aprueba este mismo PR (dogfooding D4 sobre E1a).

### `feat/e1b-skill-branch-plan-interview` — ✅ (PR pendiente)

Segunda rama de Fase E — completa el par de skills de orquestación Fase -1 que E1a dejó abierto. `branch-plan` produce el paquete de seis entregables para aprobación del usuario; `deep-interview` clarifica scope socráticamente cuando la rama tiene ambigüedad conceptual real. Ambas respetan el contrato canonizado en E1a (primitive oficial, logging best-effort, sin markers, sin abrir ramas).

Entregables:

- `.claude/skills/branch-plan/SKILL.md` — skill Fase -1 producer. Lee `MASTER_PLAN.md § Rama <slug>`, los archivos citados en "Contexto a leer" (por rangos), `HANDOFF.md §9` si procede, y git introspection cheap (`log`/`diff`/`status`). Emite los **seis entregables** en conversación (Resumen técnico / conceptual / Ambigüedades / Alternativas / Test plan / Docs plan). **Delegación inline vía Agent tool** cuando el plan requiere leer ≥3 archivos no triviales: `subagent_type` elegido según naturaleza (Plan / code-architect / Explore) — el subagent devuelve summary al tool result, la skill lo folds en los entregables sin paste-through. **STOPS BEFORE marker** — no crea `.claude/branch-approvals/<slug>.approved`, no corre `git checkout -b`, no arranca Fase 1 (tests) ni Fase 2 (impl), no invoca `deep-interview` automáticamente (sólo sugiere opt-in en la sección de Ambigüedades). Logea via helper compartido (step 7, best-effort).
- `.claude/skills/deep-interview/SKILL.md` — skill clarificadora socrática. **Opt-in estricto**: tres condiciones deben valerse (invocación explícita del usuario + ambigüedad conceptual real + usuario disponible para dialog); si cualquiera falla → respuesta de una línea + log `status: declined` + salida silenciosa. Lectura minimal-only (`MASTER_PLAN § Rama`, `HANDOFF §9`, `git log -10`) — no carga `docs/ARCHITECTURE.md` ni gotchas enteros. Pregunta en **clusters de 1–3 preguntas**, máximo 3–5 clusters totales, corta antes si la ambigüedad se resuelve. Cierra con **Clarified / Still open / Recommend** y pasa por **ratification gate** antes de escribir a memoria (`type: project`) — silencio ≠ consent. **Main-strict, sin subagent** (la decisión A1.c descarta fork; el coste está en el dialog del usuario, no en reading). **No muta docs, ROADMAP, MASTER_PLAN, HANDOFF ni `.claude/rules/`** — ratificación durable va a memoria sólo con "yes, save that" explícito; durabilidad de HANDOFF sigue siendo trabajo de `writing-handoff` dentro del PR. Logea via helper compartido (step 7, best-effort; `status ∈ {declined, partial, ok}`).
- `policy.yaml` — `skills_allowed` extendido de 2 → 4 entries: `[project-kickoff, writing-handoff, branch-plan, deep-interview]`. El comentario inline actualizado para reflejar que E1b mantiene el flip (`stop-policy-check.py` sigue en enforcement vivo, ahora con 4 skills aceptadas).
- Tests (extensión, no reescritura):
  - `.claude/skills/tests/test_skill_frontmatter.py` — la constante `E1A_SKILLS` renombra a `E1_SKILLS_KNOWN = ["project-kickoff", "writing-handoff", "branch-plan", "deep-interview"]` (contract-bound, no era-bound: la próxima rama extiende la lista, no renombra el constante). Todos los tests parametrizados por slug cubren 4 skills automáticamente. Añadidas dos clases `TestBranchPlanBehavior` (3 casos: fase_minus_one_deliverables + marker_disclaim + stop_signal) y `TestDeepInterviewBehavior` (3 casos: socratic + opt_in + no_silent_mutation) que asertan sobre body text específico de cada skill — lock-down contra drift de framing.
  - `hooks/tests/test_lib_policy.py::test_real_skills_allowed_populated_by_e1a` renombrado a `_by_e1b`; la tupla esperada crece a `("project-kickoff", "writing-handoff", "branch-plan", "deep-interview")`.
  - `hooks/tests/test_skills_log_contract.py` — nuevo caso `test_all_four_e1_skills_end_to_end` en `TestEnforcementEndToEnd`. Emite una línea JSONL por cada una de las 4 skills via `log-invocation.sh`, invoca Stop hook con session_id matching, asserta allow. Guarda contra typo en policy / logger / Stop hook rompiendo el contrato 4-skills silenciosamente.

Suite global post-E1b: **639 passed + 1 skipped** (+29 vs E1a baseline de 610: 22 parametrizados adicionales via `E1_SKILLS_KNOWN` desde 2 skills → 4 + 3 branch-plan behavior + 3 deep-interview behavior + 1 log-contract integration). Sin regresión en `hooks/**` ni `.claude/skills/tests`.

Contrato fijado por la suite (extiende el contrato E1a sin reabrirlo):

- Primitive frontmatter inmutable (`name` / `description` / `allowed-tools`), sin `skill.json`, sin prefijo `pos:`, sin campos inventados. Description `"Use when ..."`. Logger best-effort step final. Cuatro skills E1 validadas por la misma suite.
- `branch-plan` **NUNCA** crea marker ni abre rama ni auto-invoca `deep-interview` — el test `TestBranchPlanBehavior::marker_disclaim` / `::stop_signal` lock down el disclaim y el STOP canonical. Delegation vía Agent tool inline es primitive-correct (la skill declara `allowed-tools` incluyendo los bash patterns que necesita; la delegación hereda del tool-call envelope del orchestrator, no requiere `context: fork` como campo de frontmatter — el primitive no lo soporta).
- `deep-interview` **es opt-in** — el test `TestDeepInterviewBehavior::opt_in` lock downs the gating (tres condiciones + stop silencioso en cualquier miss). `::no_silent_mutation` asegura el framing de ratification gate en el body. Si un futuro caller propone auto-trigger, abrir rama E1c con justificación: el framing actual es deliberado (surge de `master_repo_blueprint.md` y del rechazo explícito del usuario a skills que auto-reparsean intenciones).
- `skills_allowed` = 4 entries enforce vivo en el hook Stop; la ausencia del 5º / 6º / ... slot cuando se invoque una skill no listada seguirá produciendo deny exit 2 (contrato D6 intacto).

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Decisión A1.a `branch-plan` delegation** — elegido A1.a (Agent-tool inline delegation) vs A1.b (main-strict). Razón: Fase -1 de una rama arquitectónica puede requerir cross-file analysis no-trivial (múltiples prior gotchas + `docs/ARCHITECTURE.md § Capa X` + subtree de `generator/` o `hooks/`); cargar todo en main contamina contexto mientras la skill está activa. El primitive no soporta `context: fork` como campo frontmatter, pero delegación inline vía Agent tool es el **fork-aproximado primitive-correct** (el subagent corre en fork real; la skill sólo recibe summary). Para ramas lightweight (scope obvio + ≤2 files), la skill salta delegation y emite los seis entregables directamente en main.
- **Decisión A1.c `deep-interview` main-strict** — elegido A1.c (conversational, sin subagent). Razón: el coste de una entrevista NO está en reading (el body dice explícitamente "do NOT read `docs/ARCHITECTURE.md` top-to-bottom"); el coste está en el dialog del usuario. Un subagent intermediaría sin añadir valor y rompería la interactividad socrática. La lectura es deliberadamente minimal (`MASTER_PLAN § Rama` + `HANDOFF §9` + `git log -10`), suficiente para framing sin contamination.
- **Decisión A5.a — fix `skills.md` drift en E1b** — descartado A5.b (diferir a E1c). Razón: `.claude/rules/skills.md` antes de E1b declaraba frontmatter extendido (`user-invocable`, `disable-model-invocation`, `model`, `effort`, `context`, `agent`, `hooks`, `paths`) + prefijo `pos:` + "La skill no debe loguear por sí misma" — todo **contradice** el contrato E1a. Dejar el drift entre ramas implicaría que cualquier lectura de la rule file durante E1c / E2a surfacearía decisiones ya rechazadas. Reconciliamos en la misma rama que añade las skills cuyo body es el testigo del contrato real. **Cambios al rule file**: eliminado el bloque `Frontmatter obligatorio` inflado, reemplazado por referencia al shape canónico documentado en `skills-map.md` (fuente única); `Logging` reescrito para describir el patrón `log-invocation.sh` + best-effort; corrección `/pos:kickoff` → `project-kickoff` y `/pos:handoff-write` → `writing-handoff` (eco del rename canonicalizado en E1a pero que faltaba propagar aquí); sección `Criterios context: fork` reescrita como nota histórica (el primitive no soporta el campo; fork real sólo via delegation en Agent tool inline — ver E1b decisión A1.a).
- **Framing ajustes explícitos** (aprobados en Fase -1):
  - `branch-plan` — "no crea marker / no abre rama / no ejecuta Fase -1 auto / solo produce paquete para aprobación" aparece literal en `Scope (strict)` + `Explicitly out of scope` del body. El usuario aprueba el marker y el `git checkout -b` en su respuesta; la skill se detiene antes.
  - `deep-interview` — "opt-in real / no insiste / resume y se detiene / no muta docs/memoria salvo ratificación del usuario" aparece literal en `Framing` + `Failure modes` + `Explicitly out of scope` del body. El step 2 dedicado a "User gives one-word / empty answers for two consecutive clusters → assume disengagement" cierra el caso "usuario no quiere seguir pero no lo dice explícito".
- **No se tocan E1a artifacts** — `project-kickoff` y `writing-handoff` quedan intactos; E1b sólo extiende la allowlist + añade dos skills nuevas + fixes de rule file. Regresión E1a cubierta por los mismos tests parametrizados (que ahora corren 4 vs 2 pero sin renombrar nada).

**Criterio de salida**: 639 tests verdes + 1 skip intencional en todas las suites (`hooks/tests` + `.claude/skills/tests`). E1a regression intacto (los tests parametrizados que cubrían `project-kickoff` / `writing-handoff` siguen pasando; la constante renombrada los sigue cubriendo); `test_real_skills_allowed_populated_by_e1b` flippa el pinpoint de la tupla 2→4. Docs-sync dentro del PR (ROADMAP + HANDOFF + MASTER_PLAN § Rama E1b + `.claude/rules/skills-map.md` canonicalizando `/pos:branch-plan` → `branch-plan` y `/pos:deep-interview` → `deep-interview` + `.claude/rules/skills.md` reconciliado con el contrato E1a). El hook `pre-pr-gate.py` aprueba este mismo PR (dogfooding D4 sobre E1b).

### `feat/e2a-skill-review-simplify` — ✅ (PR pendiente)

Tercera rama de Fase E — **primer par del bloque calidad**. Cierra el ciclo pre-PR con dos skills que se orquestan en orden canónico `simplify → pre-commit-review`: primero reduce el diff (redundancia / ruido / complejidad accidental / abstracción prematura), luego el review opera sobre el diff ya ligero. Ambas heredan íntegro el contrato primitive-minimal de E1a/E1b y lo extienden con patrones nuevos (writer-scoped-al-diff + Agent-tool hybrid delegation).

Entregables:

- `.claude/skills/pre-commit-review/SKILL.md` — skill delegadora. Scope: `Read`/`Grep`/`Bash(git log/diff/status/merge-base)` sobre la rama; **delega el análisis pesado** al subagent `code-reviewer` vía Agent tool inline, pasando context preparado en main (branch kickoff + scope + invariantes citados en `.claude/rules/*.md` cuyos `paths:` solapen el diff) + `git diff main...HEAD` completo + asks explícitos (bugs + logic + security + scope adherence + invariant violations). El subagent corre en fork real y devuelve summary confidence-filtered; el main folds (dedup + file:line + severity order + veredicto `clean to PR | findings blocking | findings advisory only`) — **no paste-through**. **Nunca edita, nunca abre PR, nunca sustituye a `simplify`**. Logea via helper compartido.
- `.claude/skills/simplify/SKILL.md` — skill reductora writer-scoped. Scope: `Read`/`Grep`/**`Edit`** (diferencia clave con `pre-commit-review`) + git introspection. Deriva el scope en step 1 con `git diff --name-only main...HEAD` y **todo `Edit` call valida que el `file_path` pertenezca a esa lista**; si no, reclassify as `skip (out of scope)`. **No crea archivos nuevos** (si una reducción lo requeriría, emite nota), **no toca archivos fuera del diff**, **no cambia comportamiento**, **no busca bugs** (ese es `pre-commit-review`), **no hace refactor mayor**. Cierra con reporte dos partes: "qué simplificó / what was simplified" + "qué decidió no tocar / what it chose not to touch". Logea via helper compartido.
- `policy.yaml.skills_allowed` extendida 4 → 6: `[project-kickoff, writing-handoff, branch-plan, deep-interview, pre-commit-review, simplify]`. Comentario inline updated (`E1a scaffold → E1b 4 skills → E2a 6 skills`). `stop-policy-check.py` continúa en enforcement live, ahora con 6 skills aceptadas.
- Tests (extensión, no reescritura):
  - `.claude/skills/tests/test_skill_frontmatter.py` — constante `E1_SKILLS_KNOWN` renombrada a `ALLOWED_SKILLS` (contract-bound al allowlist entero) + extendida 4 → 6. Todos los tests parametrizados (11 por skill × 6 skills = 66 automáticos) cubren el contrato sin cambio. Añadidas dos clases: `TestPreCommitReviewBehavior` (3 casos: `test_delegates_to_code_reviewer` + `test_scope_is_branch_diff` + `test_body_disclaims_writing_and_replacement`) + `TestSimplifyBehavior` (4 casos: `test_allowed_tools_includes_edit` + `test_scope_limited_to_branch_diff_no_new_files` + `test_body_frames_reducer_not_bug_finder` + `test_body_reports_what_simplified_and_what_skipped`).
  - `hooks/tests/test_lib_policy.py::test_real_skills_allowed_populated_by_e1b` renombrado a `_by_e2a`; tupla esperada crece 4 → 6 entries.
  - `hooks/tests/test_skills_log_contract.py::test_all_four_e1_skills_end_to_end` renombrado a `test_all_six_e1_e2a_skills_end_to_end`; allowlist + loop cubren las 6 skills.

Suite global post-E2a: **668 passed + 1 skipped** (+29 vs baseline E1b de 639: 22 parametrizados por `ALLOWED_SKILLS` 4→6 + 3 pre-commit-review behavior + 4 simplify behavior; 1 log-contract integration actualizado + 1 `_populated_by_e2a` renombrado. El skip es el D5 intencional `TestIntegrationDiffUnavailable` por subprocess-no-cover). Sin regresión en `hooks/**` ni E1a/E1b regression.

Contrato fijado por la suite (extiende E1a + E1b sin reabrirlos):

- Primitive frontmatter inmutable (`name` / `description` / `allowed-tools`), sin `skill.json`, sin prefijo `pos:`, sin campos inventados. Precedentes E1a + E1b intactos.
- `pre-commit-review` **nunca** reescribe código, **nunca** aplica fixes, **nunca** abre PR, **nunca** sustituye a `simplify`. Test `TestPreCommitReviewBehavior::test_body_disclaims_writing_and_replacement` lock downs los 4 tokens literales requeridos en el body (`findings` + `does not rewrite` o equivalente + `simplify` + `does not replace` / `not a substitute`). Delegation pattern `code-reviewer` + `subagent_type` + `git diff main...HEAD` lock down por `test_delegates_to_code_reviewer` + `test_scope_is_branch_diff`.
- `simplify` **nunca** crea archivos, **nunca** toca archivos fuera del diff, **nunca** cambia comportamiento, **nunca** busca bugs, **nunca** hace refactor mayor. Tests `TestSimplifyBehavior` × 4 lock down cada disclaim literal + la derivación determinista del scope (`git diff --name-only main...HEAD` en el body) + la forma del reporte final (lista de simplificado + lista de skipped con razón).
- `ALLOWED_SKILLS = 6` entries enforce vivo. Invocar una skill no listada sigue produciendo deny exit 2 (contrato D6 intacto).
- Canonical order `simplify → pre-commit-review` documentada en ambos bodies. Ambas disclaim replacement mutuo.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Decisión A1.b writer-scoped strict** (vs A1.a read-only proponer + user aplica): `simplify` edita directamente archivos del diff; scope derivado via `git diff --name-only main...HEAD`; disciplina declarada en body + locked via 4 behavior tests. Razón: evitar fricción de un gate adicional en un ciclo pre-PR ya largo; si aparece drift en la disciplina, remedy es PR correctiva, no cambio de patrón. Tradeoff consciente: el usuario no ve diff de simplify para pre-approval.
- **Decisión A2.c hybrid delegation** (vs A2.a all-main / A2.b all-subagent): main prepara context ligero (kickoff commit + invariantes) + subagent analiza diff completo + main folds summary. A2.a descartado por coste en contexto (full diff + invariantes en main); A2.b descartado porque el subagent no vería invariantes repo-specific. Hybrid captura lo mejor. Precedente directo: `branch-plan` (E1b A1.a) delegation pattern.
- **Decisión A3.a rename atómico** (vs A3.b mantener `E1_SKILLS_KNOWN` + añadir `E2_SKILLS_KNOWN`): `ALLOWED_SKILLS` contract-bound al allowlist entero, no a la era. Dos constantes coexistiendo propagaría el envejecimiento a cada fase futura. Rename trae update coordinado de `.claude/rules/skills.md` línea 61.
- **Decisión A5 hardcode subagent name + disclaimer** (vs helper runtime con capability resolution): una sola skill consumidora hoy; abstracción prematura rechazada por regla #7 CLAUDE.md. Disclaimer literal en el body apunta a `.claude/rules/skills.md § Fork / delegación`; fallback a `general-purpose` declarado si el runtime enum no expone `code-reviewer`. Reabrir si E2b `audit-plugin` u otra skill aporta segunda repetición.
- **Framing ajustes explícitos** (aprobados en Fase -1):
  - `simplify` body carries literal tokens locked by tests: `git diff --name-only`, `main...HEAD`, `does not create new files`, `outside the diff`, `does not find bugs`, `does not change behavior`, `no major refactor`, tokens de targets (`redundan` / `accidental` / `prematura` / `ruido` / `noise`) + tokens de reporte (`qué simplificó` / `what was simplified` + `qué decidió no tocar` / `what it chose not to touch`). Step 4 lleva la regla dura: "Scope check every call: the `file_path` must match an entry from step 1. If it doesn't, do NOT edit — re-classify as `skip (out of scope)`".
  - `pre-commit-review` body carries literal: "does not rewrite code", "does not apply fixes", "does not replace `simplify` and is not a substitute for it" + bloque de Delegation hybrid con el disclaimer del subagent name hardcoded + fallback a `general-purpose`.
- **YAML parse gotcha atrapado en GREEN**: descripción v1 de `simplify` contenía `"Writer scoped: edits files..."` — el `: ` activaba el parser YAML como mapping-separator y rompía el frontmatter entero. Fix: em-dash `Writer-scoped — edits files...`. Lección para futuras skills: evitar `palabra: palabra` dentro de descriptions.

**Criterio de salida**: 668 verdes + 1 skip intencional. E1a + E1b + D1..D6 regression intacta. `test_real_skills_allowed_populated_by_e2a` flippa el pinpoint de la tupla 4→6. `stop-policy-check.py` sigue en enforcement live sin cambio de código — sólo con allowlist ampliada. Docs-sync dentro del PR (ROADMAP § E2a + HANDOFF §1/§9 + §15 nuevo + MASTER_PLAN § Rama E2a + `.claude/rules/skills-map.md` canonicalizando 2 filas Calidad + `.claude/rules/skills.md` rename `E1_SKILLS_KNOWN` → `ALLOWED_SKILLS` + notas sobre E2a como primera consumidora de `code-reviewer` y `simplify` como segunda writer-scoped tras `writing-handoff`). `docs/ARCHITECTURE.md` **no** requerido (E2a no toca `generator/` ni `hooks/`). El hook `pre-pr-gate.py` aprueba este mismo PR (dogfooding D4 sobre E2a).

## Convenciones de este archivo

- Una fila por rama. `⏳` pendiente, `🔄` en vuelo, `✅` completada, `❌` abandonada, `🚫` bloqueada.
- Columna PR: `#N` o `—` si no aplica (commit directo, sólo para bootstrap de Fase A).
- Actualización: **dentro de la rama que cierra** (docs-sync Fase N+3). No post-merge.

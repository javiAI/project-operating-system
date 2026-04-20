# ROADMAP — project-operating-system

Estado vivo. Cada fila refleja una rama de [MASTER_PLAN.md](MASTER_PLAN.md).

## Progreso general

| Fase | Descripción | Estado |
|---|---|---|
| A | Skeleton & bootstrap | ✅ |
| B | Cuestionario + profiles + runner | ✅ |
| C | Templates + renderers | 🔄 en curso (C1) |
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
| `feat/c1-renderers-core-docs` | CLAUDE/MASTER_PLAN/ROADMAP/HANDOFF/AGENTS/README renderers + pipeline + `--out`/`--dry-run` wire-up | 🔄 abierta | (por abrir) |
| `feat/c2-renderers-policy-rules` | policy.yaml + rules path-scoped | ⏳ | — |
| `feat/c3-renderers-tests-harness` | Test harness por stack | ⏳ | — |
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

### `feat/c1-renderers-core-docs` — en curso

Scope (ver [MASTER_PLAN.md § Rama C1](MASTER_PLAN.md)):

- 6 renderers puros en `generator/renderers/{claude-md,master-plan,roadmap,handoff,agents,readme}.ts`, cada uno `render(profile: Profile): FileWrite[]`.
- 6 templates Handlebars en `templates/*.hbs`.
- `generator/lib/handlebars-helpers.ts` (`eq`, `neq`, `includes`, `kebabCase`, `upperFirst`, `jsonStringify`).
- `generator/lib/render-pipeline.ts` — orquestador; **falla explícitamente** ante colisión de paths.
- `generator/lib/profile-model.ts` — dotted-answers → objeto nested para templates.
- Wire-up de `--out <dir>` y `--dry-run` en `generator/run.ts`. Sin flags = `--validate-only` (compat).
- Snapshots por (profile × template) = 18 en `generator/__snapshots__/`.
- Tests semánticos mínimos por renderer (paths emitidos + strings críticas) **además** de snapshots.
- Coverage ≥85%.

**Decisiones Fase -1 (aprobadas)**:

- User-specific fields faltantes (`identity.name|description|owner`) → renderer inyecta placeholders literales `TODO(identity.<campo>)` + warning. Aplica a `--dry-run` y `--out`. No bloquea emisión.
- `.claude/rules/docs.md.hbs` **diferido a C2** (scope C2 cubre `.claude/rules/*.md`). Carry-over Fase N+7 en C1 solo afecta `HANDOFF.md.hbs` + `AGENTS.md.hbs`.
- `--out` soporta subdirectorios desde el primer día (`FileWrite.path` relativo + `mkdir -p`). Evita refactor en C2.
- `FileWrite` shape mínimo: `{ path: string; content: string }`. Sin `mode`. Bits de permisos se añaden en C5 cuando apliquen.
- `--force` fuera de scope en C1. `--out` sobre dir no vacío → exit 3 (según [.claude/rules/generator.md:56](.claude/rules/generator.md)).
- Commit 1 de la rama = pre-kickoff chore (docs-sync B3→✅, HANDOFF §1/§9/§10, ROADMAP, MASTER_PLAN §C1) + kickoff block. **No parte funcional de renderers** — la implementación arranca en commit 2 con TDD estricto.

## Convenciones de este archivo

- Una fila por rama. `⏳` pendiente, `🔄` en vuelo, `✅` completada, `❌` abandonada, `🚫` bloqueada.
- Columna PR: `#N` o `—` si no aplica (commit directo, sólo para bootstrap de Fase A).
- Actualización: **dentro de la rama que cierra** (docs-sync Fase N+3). No post-merge.

# ROADMAP — project-operating-system

Estado vivo. Cada fila refleja una rama de [MASTER_PLAN.md](MASTER_PLAN.md).

## Progreso general

| Fase | Descripción | Estado |
|---|---|---|
| A | Skeleton & bootstrap | ✅ |
| B | Cuestionario + profiles + runner | ⏳ pendiente |
| C | Templates + renderers | ⏳ pendiente |
| D | Hooks (Python) | ⏳ pendiente |
| E1 | Skills orquestación | ⏳ pendiente |
| E2 | Skills calidad | ⏳ pendiente |
| E3 | Skills patterns + tests | ⏳ pendiente |
| F | Audit + selftest + marketplace | ⏳ pendiente |

## Ramas

| Rama | Scope breve | Estado | PR |
|---|---|---|---|
| `feat/a-skeleton` | Bootstrap estructura + docs canónicos + policy | ✅ | — (commit inicial sin PR) |
| `feat/b1-questionnaire-schema` | Schema + questions YAML + validator | ⏳ siguiente | — |
| `feat/b2-profiles-starter` | nextjs-app / agent-sdk / cli-tool | ⏳ | — |
| `feat/b3-generator-runner` | `generator/run.ts` + zod + token budget check | ⏳ | — |
| `feat/c1-renderers-core-docs` | CLAUDE/MASTER_PLAN/ROADMAP/HANDOFF/AGENTS/README renderers | ⏳ | — |
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

## Convenciones de este archivo

- Una fila por rama. `⏳` pendiente, `🔄` en vuelo, `✅` completada, `❌` abandonada, `🚫` bloqueada.
- Columna PR: `#N` o `—` si no aplica (commit directo, sólo para bootstrap de Fase A).
- Actualización: **dentro de la rama que cierra** (docs-sync Fase N+3). No post-merge.

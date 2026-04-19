# AGENTS — reglas de ejecución autónoma

> Destinado a LLMs (Claude Code) que operan en este repo. Las reglas aquí son vinculantes.

## Lectura obligatoria (en orden)

1. [CLAUDE.md](CLAUDE.md)
2. Este archivo.
3. [HANDOFF.md](HANDOFF.md)
4. Sección específica de la rama actual en [MASTER_PLAN.md](MASTER_PLAN.md)
5. Path-scoped rules en [.claude/rules/](.claude/rules/) se cargan automáticamente según archivos tocados.

## Reglas no negociables

1. **Fase -1 siempre**. Ningún `git checkout -b` sin aprobación explícita documentada + marker file.
2. **Docs dentro de la rama**. Nada de "lo documentamos después". Todo docs-sync en el mismo PR.
3. **TDD**. Test primero, implementación después. Hook lo enforza (cuando D3 esté entregado); hasta entonces, manual.
4. **Patrones antes de abstraer**. ≥2 ocurrencias documentadas en evidencia antes de helper compartido.
5. **Community tool gate**. Cualquier MCP/plugin nuevo → `/pos:audit-plugin` (o su equivalente manual si no existe todavía — seguir [docs/SAFETY_POLICY.md](docs/SAFETY_POLICY.md)).
6. **Token budget**. CLAUDE.md <200 líneas. Rules path-scoped <30KB total. Si contexto >120k, invocar `/pos:compress` (o equivalente manual).
7. **No leer lo que no vas a usar**. Cita por rango de línea. No leas `MASTER_PLAN.md` entero cuando necesitas una sección.
8. **Ejecuta skills con `context: fork`** cuando esté disponible (Fase E*). Las skills pesadas en main context rompen el presupuesto.

## Fuente de verdad por capa

| Capa | Archivo | Quién puede cambiarlo |
|---|---|---|
| Plan inmutable | `MASTER_PLAN.md` | Sólo refinamientos puntuales en Fase -1 |
| Estado vivo | `ROADMAP.md` | Cada rama actualiza su fila |
| Quickref | `HANDOFF.md` | Cada rama reescribe "Próxima rama" y "Gotchas" si aplica |
| Reglas operativas | `CLAUDE.md` | Fase E3 onwards (cuando patrones se consolidan) |
| Arquitectura | `docs/ARCHITECTURE.md` | Cada fase mayor (A, B, C, D, E1-E3, F) |
| Políticas | `policy.yaml`, `docs/SAFETY_POLICY.md`, `docs/TOKEN_BUDGET.md` | Sólo ramas explícitas (F* principalmente) |
| Patrones | `.claude/patterns/*.md` | Sólo `/pos:compound` vía PR `chore/compound-*` |

## Ejecución autónoma — "continúa"

Cuando el usuario escribe "continúa" o "siguiente":

1. Leer `git log --oneline -5` + `git status -sb`.
2. Leer ROADMAP.md → identificar próxima rama en estado ⏳.
3. Leer MASTER_PLAN.md § esa rama.
4. Leer solo los archivos citados en "Contexto a leer".
5. Ejecutar Fase -1 (§2.1 MASTER_PLAN.md).
6. **Parar. Esperar aprobación.** No crear marker sin OK explícito.

## Gate de salida por fase

Antes de considerar una rama ✅:

- [ ] Criterio de salida del MASTER_PLAN.md cumplido.
- [ ] Tests locales verdes (según `policy.yaml.lifecycle.pre_push.checks_required`).
- [ ] Coverage ≥ threshold de `policy.yaml.testing.unit.coverage_threshold`.
- [ ] CI verde (cuando esté instalado, Fase F3+).
- [ ] Docs-sync completado (ROADMAP + HANDOFF + los condicionales según paths tocados — ver `policy.yaml.lifecycle.pre_pr.docs_sync_conditional`).
- [ ] Kickoff block presente en primer commit.
- [ ] `/pos:pre-commit-review` corrido (o equivalente manual).
- [ ] `/pos:simplify` corrido antes de PR.
- [ ] PR descripción generada o escrita; reviewer asignado.

## Skills requeridas por lifecycle (ver policy.yaml)

No existen todavía (Fase E*). Hasta entonces, el LLM ejecuta los equivalentes manuales:

| Skill futura | Equivalente manual |
|---|---|
| `/pos:kickoff` | Leer HANDOFF.md §1-§4. |
| `/pos:branch-plan` | Producir el texto de Fase -1 §2.1 a mano. |
| `/pos:pre-commit-review` | Invocar subagent `code-reviewer` con diff staged. |
| `/pos:simplify` | Pasar el diff por subagent con prompt "reduce sin perder semántica". |
| `/pos:compound` | Al mergear, evaluar manualmente si `touched_paths` del profile matchea. |
| `/pos:audit-plugin` | Seguir checklist de [docs/SAFETY_POLICY.md](docs/SAFETY_POLICY.md) a mano. |

## Cuando algo falla

1. **Hook no dispara** (porque no existe aún): documentar en kickoff que el manual replacement fue aplicado.
2. **Test falla**: no commentar ni `.skip`. Arreglar o documentar en kickoff como blocker.
3. **Marker no acepta**: revisar sanitización del slug (`/` → `_`, espacios → `-`).
4. **Contexto explota**: `/compact focus="..."` + memoria `project` con decisiones actuales. Nunca `/clear` con decisiones vivas.

## Lo que este repo NO hace por ti

- No commitea por ti. Siempre pide confirmación antes de `git commit` o `git push`.
- No abre PRs automáticamente (Fase F4+ tendrá `/pos:pr-description`, pero sigue requiriendo OK humano para `gh pr create`).
- No instala dependencias sin preguntar.
- No modifica `main` directamente (salvo Fase A bootstrap documentado).

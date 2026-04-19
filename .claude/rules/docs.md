---
name: docs
description: Reglas al tocar docs del meta-repo (no aplica a templates/)
paths:
  - "docs/**"
  - "MASTER_PLAN.md"
  - "ROADMAP.md"
  - "HANDOFF.md"
  - "AGENTS.md"
  - "README.md"
  - "CLAUDE.md"
---

# Reglas — Docs del meta-repo

## Principio

**Docs de este repo ≠ docs del repo generado.** Los segundos viven en `templates/`. Si editas un archivo bajo `templates/`, estás diseñando lo que verán los usuarios — no te rijas por estas reglas, sino por las de `templates.md`.

## Archivos canónicos (evitar duplicación)

| Archivo | Propósito |
|---|---|
| `MASTER_PLAN.md` | Plan inmutable de ramas del propio meta-repo. Se edita sólo para actualizar el estado de la rama que acabas de completar. |
| `ROADMAP.md` | Estado vivo. Una sola tabla + progreso por fase. |
| `HANDOFF.md` | Quickref 30s. Se reescribe al final de cada rama. |
| `AGENTS.md` | Reglas de ejecución autónoma. Cambia raramente. |
| `CLAUDE.md` | <200 líneas. Reglas del repo. |
| `docs/ARCHITECTURE.md` | Decisiones de diseño canonicalizadas. Evoluciona con cada fase mayor. |
| `docs/SAFETY_POLICY.md` | Política de vetting de community tools. |
| `docs/TOKEN_BUDGET.md` | Reglas de eficiencia. |
| `docs/KNOWN_GOOD_MCPS.md` | Lista allowed MCPs para opt-in. |

No crear `NOTES.md`, `TODO.md`, `PLAN-V3.md` ni variantes. Usa memoria persistente para eso.

## Reglas de escritura

1. **Enlaces relativos** siempre. `[texto](docs/X.md#seccion)`, nunca URLs absolutas al propio repo.
2. **Sin timestamps** ni "updated on YYYY-MM-DD" en el cuerpo (usa git blame).
3. **Sin emojis** salvo `✅ ❌ ⚠️` en tablas de estado.
4. **Español**. Consistente con el estilo del usuario.
5. **Líneas ≤120 chars**. Prefiere párrafos cortos.
6. **Citación de código**: `path/al/archivo.ts:42-58`, nunca copia-pega extensa.

## Docs-sync en cada rama

Antes de cerrar la rama (Fase N+3), validar:

- `ROADMAP.md` refleja el nuevo estado (añadir fila o marcar ✅).
- `HANDOFF.md` sección "Próxima rama" apunta a la siguiente.
- `MASTER_PLAN.md § Rama X` — si la rama cerró con decisiones que amplían o contradicen el plan, actualizar la sección de esa rama + explicar en kickoff.
- `docs/ARCHITECTURE.md` — si la rama introdujo un patrón estructural nuevo, añadir sub-sección.
- `.claude/rules/*.md` — si la rama introdujo patrones que se repetirán, crear o actualizar rule path-scoped.
- `docs/KNOWN_GOOD_MCPS.md` — si la rama aprobó un MCP vía `/pos:audit-plugin`.

El hook `pre-pr-gate.sh` verifica que al menos `ROADMAP.md` y `HANDOFF.md` están en el diff de la rama. Si la rama tocó `generator/**` o `hooks/**`, también exige diff en `docs/ARCHITECTURE.md` o justificación (`// no-arch-change: <reason>`).

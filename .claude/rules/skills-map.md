---
name: skills-map
description: Mapa canónico de skills del plugin pos con lifecycle, modelo y contexto
paths: []
---

# Skills-map — plugin `pos`

Mapa de referencia. Se actualiza a medida que cada Fase E* entrega skills.

## Core (entregado en E1)

| Skill | Lifecycle | Modelo | Context | Qué hace |
|---|---|---|---|---|
| `/pos:kickoff` | inicio de sesión | sonnet | main | Snapshot 30s + detecta siguiente rama |
| `/pos:branch-plan` | Fase -1 | opus | fork | Resumen técnico/conceptual + ambigüedades + alternativas |
| `/pos:deep-interview` | Fase -1 (alto riesgo) | opus | fork | Socratic questioning para clarificar scope |
| `/pos:handoff-write` | pre-/clear o /compact | sonnet | main | Persiste estado actual en HANDOFF.md + memoria |

## Calidad (entregado en E2)

| Skill | Lifecycle | Modelo | Context | Qué hace |
|---|---|---|---|---|
| `/pos:pre-commit-review` | Fase N+2 | sonnet | fork | Review con agent code-reviewer |
| `/pos:simplify` | Fase N+1 | sonnet | fork | Reducción de código/docs antes de PR |
| `/pos:compress` | on-demand (contexto >120k) | haiku | fork | Comprime docs/logs largos |
| `/pos:audit-plugin` | antes de instalar MCP/plugin | sonnet | fork | GO/NO-GO por política SAFETY_POLICY.md |

## Pattern + Test (entregado en E3)

| Skill | Lifecycle | Modelo | Context | Qué hace |
|---|---|---|---|---|
| `/pos:compound` | post-merge (trigger by touched_paths) | opus | fork | Extrae patrones reutilizables |
| `/pos:pattern-audit` | Fase N+3 | sonnet | fork | Valida no hay drift sobre patrones activos |
| `/pos:test-scaffold` | al crear archivo sin test pair | sonnet | fork | Genera skeleton de tests |
| `/pos:test-audit` | on-demand / pre-release | sonnet | fork | Detecta flaky, orphan, trivial assertions |
| `/pos:coverage-explain` | cuando coverage falla | haiku | main | Explica por qué + targets mínimos |

## Audit + Release (entregado en F)

| Skill | Lifecycle | Modelo | Context | Qué hace |
|---|---|---|---|---|
| `/pos:audit-session` | semanal / on-demand | sonnet | fork | Compara policy.yaml vs logs reales |
| `/pos:pr-description` | pre-PR | sonnet | main | Genera descripción del PR desde commits + kickoff |
| `/pos:release` | en tag | sonnet | main | Valida versión + publica + notifica |

## Disabled until earned

Ninguna skill adicional se registra en `policy.yaml` hasta que pasa `/pos:audit-plugin --self`.

---
name: skills-map
description: Mapa canónico de skills del plugin pos con lifecycle, modelo y contexto
paths: []
---

# Skills-map — plugin `pos`

Mapa de referencia. Se actualiza a medida que cada Fase E* entrega skills.

## Shape canónico (fijado en E1a)

Cada skill vive en `.claude/skills/<slug>/SKILL.md` con frontmatter YAML minimal del primitive oficial de Claude Code Skills:

```yaml
---
name: <slug-kebab-case>               # debe coincidir con el nombre del directorio. SIN prefijo `pos:`.
description: Use when <disparadores>. # "Use when …" — selección eligible por el modelo, NO trigger garantizado.
allowed-tools:                        # opcional. Lista YAML (no string). Ej: Read, Bash(git log:*), Bash(.claude/skills/_shared/log-invocation.sh:*)
  - Read
  - Bash(git log:*)
---
```

**No inventar campos** más allá de `name` / `description` / `allowed-tools`. Campos como `context:` / `model:` / `agent:` / `effort:` / `hooks:` / `user-invocable:` propuestos en Fase -1 v1 de E1a fueron rechazados por no tener documentación oficial citable en el SDK actual. Si una versión futura del SDK los añade, citar la fuente antes de introducirlos (rama propia).

**Logging best-effort**: toda skill termina con una llamada Bash a `.claude/skills/_shared/log-invocation.sh <name> <status>` — emite una línea JSONL a `.claude/logs/skills.jsonl` con shape estable `{ts, skill, session_id, status}`. Si el modelo omite el step, el sistema pierde traza pero no rompe (silencio ≠ violación para `stop-policy-check.py`).

**Allowlist enforcement**: `policy.yaml.skills_allowed` debe listar cada skill que el repo acepta invocar. Ausencia = el hook Stop pasa en modo `deferred`. Lista poblada = enforcement live (invocar una skill no-allowlisted deniega el Stop).

## Core (entregado en E1)

| Skill | Lifecycle | Modelo | Context | Qué hace |
|---|---|---|---|---|
| `project-kickoff` | inicio de sesión (`/kickoff`, "continúa", "arranca la siguiente rama") | sonnet | main | Snapshot ≤12 líneas (branch, phase, last merge, next branch, warnings) + STOP antes de Fase -1 |
| `branch-plan` | Fase -1 (rama nueva) | sonnet + Agent-tool inline delegation (pick subagent by capability; Claude Code defaults today: `Plan` / `code-architect` / `Explore`) cuando lectura ≥3 files no triviales | main (con delegation inline) | Produce los 6 entregables (técnico / conceptual / ambigüedades / alternativas / test plan / docs plan). **NO** crea marker, **NO** abre rama, **NO** auto-invoca `deep-interview` (sólo sugiere opt-in). |
| `deep-interview` | Fase -1 opt-in (alto riesgo conceptual) | sonnet | main (conversacional, sin subagent) | Socratic questioning para clarificar scope. Opt-in estricto (tres condiciones). Clusters 1–3 preguntas × máximo 3–5 clusters. Cierra con Clarified/Still open/Recommend + ratification gate antes de escribir memoria. **NO** muta docs / ROADMAP / MASTER_PLAN / HANDOFF / rules. |
| `writing-handoff` | pre-`/clear` o `/compact` / cierre de rama | sonnet | main | Edita HANDOFF §1/§9/§6b/gotchas + persiste decisiones durables a memoria; NO toca MASTER_PLAN/ROADMAP/docs |

## Calidad (entregado en E2)

Canonical order pre-PR: **`simplify → pre-commit-review`**. Reduce primero, review después sobre el diff ya ligero. Ambas skills disclaim literal que no se sustituyen entre sí (running `pre-commit-review` no obvia `simplify`; running `simplify` no obvia `pre-commit-review`).

| Skill | Lifecycle | Modelo | Context | Qué hace |
|---|---|---|---|---|
| `simplify` | Fase N+1 (pre-PR) | sonnet | main (writer-scoped) | Reduce redundancia / ruido / complejidad accidental / abstracción prematura en archivos ya presentes en `git diff --name-only main..HEAD`. **Writer-scoped strict**: edita vía `Edit` sólo archivos del diff; no crea archivos nuevos; no toca archivos fuera del diff; no cambia comportamiento; no busca bugs; no hace refactor mayor. Cierra con reporte "qué simplificó / what was simplified" + "qué decidió no tocar / what it chose not to touch". |
| `pre-commit-review` | Fase N+2 (pre-PR) | sonnet | main + Agent-tool hybrid delegation (`code-reviewer`) | Main prepara context (branch kickoff + invariantes de `.claude/rules/*.md` aplicables al diff); delega vía `Agent(subagent_type="code-reviewer", ...)` con `git diff main..HEAD` completo + asks explícitos (bugs + logic + security + scope adherence + invariant violations); subagent corre en fork real y devuelve summary confidence-filtered; main folds (dedup + file:line + severity order + veredicto de una línea). Fallback a `general-purpose` si el runtime enum no expone `code-reviewer`. **Nunca edita, nunca abre PR, nunca sustituye a `simplify`**. |
| `compress` | on-demand (contexto >120k) | sonnet | main | Read-only advisory planner: propone qué `.claude/logs/*.jsonl` comprimir (edad, tamaño, importancia). No edita ni elimina archivos; usuario decide. E2b advisory-only. |
| `audit-plugin` | antes de instalar community tool (MCP/plugin) | sonnet | main | Read-only advisory gate: audita contra SAFETY_POLICY.md 6-checklist, retorna GO/NO-GO/NEEDS_MORE_INFO. No instala, no enforza, no modifica policy.yaml. E2b advisory-only; enforcement diferido. |

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

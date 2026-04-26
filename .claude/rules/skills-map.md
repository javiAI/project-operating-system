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
| `pre-commit-review` | Fase N+2 (pre-PR) | sonnet | main + Agent-tool hybrid delegation (`pos-code-reviewer` plugin agent post-F2) | Main prepara context (branch kickoff + invariantes de `.claude/rules/*.md` aplicables al diff); delega vía `Agent(subagent_type="pos-code-reviewer", ...)` con `git diff main...HEAD` completo + asks explícitos (bugs + logic + security + scope adherence + invariant violations); subagent corre en fork real y devuelve summary confidence-filtered; main folds (dedup + file:line + severity order + veredicto de una línea). Fallback a `general-purpose` si el runtime no expone agents del plugin. **Nunca edita, nunca abre PR, nunca sustituye a `simplify`**. |
| `compress` | on-demand (contexto >120k) | sonnet | main | Read-only advisory planner: propone qué `.claude/logs/*.jsonl` comprimir (edad, tamaño, importancia). No edita ni elimina archivos; usuario decide. E2b advisory-only. |
| `audit-plugin` | antes de instalar community tool (MCP/plugin) | sonnet | main | Read-only advisory gate: audita contra SAFETY_POLICY.md 6-checklist, retorna GO/NO-GO/NEEDS_MORE_INFO. No instala, no enforza, no modifica policy.yaml. E2b advisory-only; enforcement diferido. |

## Pattern + Test (entregado en E3)

| Skill | Lifecycle | Modelo | Context | Qué hace |
|---|---|---|---|---|
| `compound` | post-merge (trigger by touched_paths, policy-driven) | opus | main (writer-scoped strict) | Lee merged diff; delega análisis a `pos-architect` plugin agent post-F2 (fallback `general-purpose`); escribe patrones a `.claude/patterns/` (formato canónico: `# Pattern:` + secciones `##`). No refactoring de código, solo propuestas de patrones. **STOP**: usuario revisa + aprueba merge de patrón. |
| `pattern-audit` | Fase N+3 post-merge (manual invoke) | sonnet | main (main-strict, no delegation) | Lee entradas `.claude/patterns/`; busca signals en codebase (Grep/Bash); detecta drift (signal/examples/rule inconsistency). Emite reporte diagnóstico sin mutar archivos. **STOP**: usuario revisa y decide acción (actualizar patrón / invocar compound). |
| `test-scaffold` | al crear archivo sin test pair | sonnet | main (writer-scoped strict) | Detecta convención de tests (co-located vs `tests/`) sobre el repo; si ≥80% claro → genera **solo** el test pair skeleton del archivo source que el usuario provee; si ambigua → STOP + propone opciones. **NO** modifica source code, **NO** ejecuta pytest/vitest, **NO** modifica thresholds/config. Allowed-tools: `Glob`, `Grep`, `Read`, `Write`, `Bash(find:*)`, `Bash(git grep:*)`, logger. |
| `test-audit` | on-demand / pre-release | sonnet | main (main-strict, no delegation) | Read-only advisory: declara **candidate signals** (no "detecta") via static analysis sobre archivos test — flaky risk (asserts en loops/conditionals), orphan tests (imports a paths que no existen), trivial assertions (`assert True`/`False`/empty). **NO** ejecuta pytest/vitest, **NO** modifica archivos. Cierra con disclaim de no-exhaustividad. Allowed-tools: `Glob`, `Grep`, `Read`, `Bash(find:*)`, `Bash(git grep:*)`, `Bash(wc:*)`, logger. |
| `coverage-explain` | cuando coverage falla | sonnet | main (main-strict, no delegation) | Read-only advisory: lee reportes existentes de coverage (lcov.json / pytest-cov JSON / NYC / htmlcov), declara estrategia de parsing, explica gaps por archivo, propone targets mínimos viables (no mandatorios). **NO** ejecuta `npm run test-coverage`/`pytest --cov`, **NO** modifica `coverage.threshold`/`pyproject.toml`/tests. Allowed-tools: `Glob`, `Grep`, `Read`, `Bash(find:*)`, logger. |

## Audit + Release (entregado en F)

| Skill | Lifecycle | Modelo | Context | Qué hace |
|---|---|---|---|---|
| `audit-session` | on-demand (manual invoke) | sonnet | main (main-strict, no delegation) | Read-only advisory: compara 3 superficies de `policy.yaml` contra `.claude/logs/` reales — (1) `skills_allowed` ↔ `skills.jsonl` invocations distintas (con normalization `pos:<slug>` ↔ `<slug>`); (2) `lifecycle.<gate>.hooks_required` ↔ `<hook>.jsonl` (existencia + nonempty); (3) `audit.required_logs` ↔ existencia + nonempty + mtime. **Declares candidate signals** (no "detecta", no auto-fixea). Reporte estructurado por surface (3 secciones + summary line con counts). 30-day review window declarado como **textual guidance** para el lector humano (no date arithmetic, no filtrado por timestamp). **NO** modifica `policy.yaml`, **NO** rota/trunca/edita logs, **NO** delega a subagent (main-strict por design — comparación local + barata). Allowed-tools: `Glob`, `Grep`, `Read`, `Bash(find:*)`, `Bash(wc:*)`, logger. |
| `/pos:pr-description` | pre-PR | sonnet | main | Genera descripción del PR desde commits + kickoff |
| `/pos:release` | en tag | sonnet | main | Valida versión + publica + notifica |

## Subagents del plugin (entregado en F2)

Plugin-owned subagents en `agents/<slug>.md`. **Shape distinto al skill primitive**: frontmatter `{name, description, tools, model}`, donde `tools` es comma-separated string (oficial Claude Code subagent format), no YAML list `allowed-tools`. Sin campos inventados. Namespace `pos-*` obligatorio para evitar colisión con built-ins de Claude Code (`code-reviewer`, `code-architect`, `Plan`, `Explore`, `general-purpose`) y con user/project agents externos.

| Agent | Consumido por | Modelo | Capacidad | Hard limits |
|---|---|---|---|---|
| `pos-code-reviewer` | `pre-commit-review` (E2a) | sonnet | Branch-diff review: bugs / logic errors / security vulnerabilities / scope adherence / invariant violations. Output findings agrupados por severidad (blocker/high/medium/nit), confidence-filtered, `file:line` refs. | No `Edit`, no `Write`, no PR, no invocación de otras skills/subagents. |
| `pos-architect` | `compound` (E3a) | sonnet | Pattern extraction (≥2 repeticiones, regla #7) + architectural design + cross-file consistency. Output patterns en formato canónico (Name/Context/Signal/Rule/Examples/Rationale) listo para fold en `.claude/patterns/<slug>.md`. | No refactor, no `Edit`, no overwriting de patterns existentes. |

**Contract tests** en `agents/tests/test_agent_frontmatter.py` parametrizados por `ALLOWED_AGENTS = ["pos-code-reviewer", "pos-architect"]`: 4 clases (structure, frontmatter keys ⊆ `{name, description, tools, model}` + namespace `pos-*` + tools comma-separated string + model ∈ `{sonnet, opus, haiku}`, body substantive >100 chars, capability surfaces).

**Fallback `general-purpose`** explícito en bodies de skills consumidoras — protege contra runtimes que no exponen agents del plugin (Claude Code antes de discovery del directorio `agents/`, entornos minimal).

**Diferidos en F2 (regla #7 CLAUDE.md)**:

- `pos-auditor` — sin consumer real hoy. Reabrir cuando una skill futura lo requiera.
- `policy.yaml.agents_allowed` — sin enforcement consumer (Stop hook lee `skills.jsonl`, no hay log de invocaciones de subagents). Reabrir cuando un hook futuro requiera enforcement.

**Forward-compat negation**: main-strict skills (`pattern-audit` E3a, `audit-session` F1) **nunca** deben referenciar plugin subagents. Tests negation list incluye `pos-architect` / `pos-code-reviewer` desde F2.

## Disabled until earned

Ninguna skill adicional se registra en `policy.yaml` hasta que pasa `/pos:audit-plugin --self`.

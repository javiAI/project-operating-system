---
name: skills
description: Reglas cuando editas skills del plugin pos (primitive oficial Claude Code Skills)
paths:
  - ".claude/skills/**"
---

# Reglas — Skills del plugin `pos`

Fijadas en E1a (primitive correction permanente) + extendidas en E1b. Fuente de verdad del shape canónico: [skills-map.md § Shape canónico](skills-map.md). Esta rule recoge **cómo trabajar** sobre skills — no duplica el contrato del frontmatter.

## Estructura

Cada skill vive en `.claude/skills/<slug>/SKILL.md`:

```
.claude/skills/<slug>/
└── SKILL.md       # único archivo obligatorio — frontmatter + cuerpo

.claude/skills/_shared/
└── log-invocation.sh   # helper compartido (E1a)

.claude/skills/tests/
└── test_skill_frontmatter.py   # contract tests parametrizados por slug
```

**No `skill.json`**. **No `scripts/` por skill** salvo que una rama futura justifique el patrón con ≥2 skills consumidoras (regla #7 CLAUDE.md). Tests de skills viven en el dir compartido `.claude/skills/tests/` — no hay `tests/` por skill.

## Frontmatter — primitive minimal

Ver [skills-map.md § Shape canónico](skills-map.md) para el shape autoritativo. Resumen operativo:

- `name` — kebab-case, coincide con el dir; **SIN prefijo `pos:`**.
- `description` — empieza case-insensitive con `"Use when …"`. Selección eligible por el modelo, NO trigger garantizado.
- `allowed-tools` — opcional. Lista YAML (no string inline). Ejemplos: `Read`, `Grep`, `Bash(git log:*)`, `Bash(.claude/skills/_shared/log-invocation.sh:*)`.

**Prohibido**: campos `context`, `model`, `agent`, `effort`, `hooks`, `user-invocable`, `disable-model-invocation`, `paths` en el frontmatter de la skill. Fueron propuestos en Fase -1 v1 de E1a y **rechazados** por no existir en el SDK oficial. Si un release futuro los documenta → cita la fuente en una rama nueva antes de introducirlos.

## Fork / delegación (sin campo `context:`)

El primitive no soporta `context: fork` declarativamente. Si una skill requiere cross-file analysis pesado (≥3 archivos no triviales), **delegar inline vía Agent tool** desde el body de la SKILL.md es el patrón correcto.

La skill debe escoger el `subagent_type` **por capacidad**, no por nombre hardcoded — los nombres concretos pueden variar entre releases/entornos. Regla operativa: inspeccionar el enum `subagent_type` de la tool `Agent` en runtime y matchear por capacidad. Desde F2 los subagents críticos para review + arquitectura son **propiedad del plugin** (definidos en `agents/<slug>.md` con namespace obligatorio `pos-*`); el resto reusan defaults built-in de Claude Code:

- **Planning independiente** (cross-check contra el plan de la skill) — Claude Code hoy: `Plan` (built-in).
- **Segunda opinión arquitectónica genérica** (crítica de diseño no-pattern-extraction) — Claude Code hoy: `code-architect` (built-in). Para pattern extraction post-merge usar `pos-architect` (ver abajo).
- **Context gathering cross-files** (explora y devuelve digest) — Claude Code hoy: `Explore` (built-in).
- **Review de diff de rama** (confidence-filtered review) — **plugin agent: `pos-code-reviewer`** (entregado en F2; ver `agents/pos-code-reviewer.md`). **Primera consumidora: `pre-commit-review` (E2a)**. Patrón: main prepara context ligero (branch kickoff + invariantes de `.claude/rules/*.md` aplicables al diff); delega via `Agent(subagent_type="pos-code-reviewer", ...)` con `git diff main...HEAD` completo + asks explícitos; subagent corre en fork real, devuelve summary confidence-filtered; main folds (dedup + file:line + severity). Hardcode del nombre `pos-code-reviewer` en el body **con disclaimer** + fallback a `general-purpose` si el runtime no expone agents del plugin — decisión A5 de E2a (una sola consumidora hoy no justifica helper runtime, regla #7 CLAUDE.md) ratificada en F2 con namespace `pos-*` para evitar colisión con built-ins.
- **Pattern extraction + cross-file design** (post-merge) — **plugin agent: `pos-architect`** (entregado en F2; ver `agents/pos-architect.md`). **Primera consumidora: `compound` (E3a)**. Patrón: main pasa diff merged + lista de patterns existentes; subagent identifica 1–3 patrones que repiten ≥2 veces y devuelve propuestas en formato canónico (Name/Context/Signal/Rule/Examples/Rationale); main folds en `.claude/patterns/<slug>.md`. Hardcode `pos-architect` con fallback `general-purpose`.
- **Fallback general** si ninguna capacidad específica encaja o el runtime no expone el agent del plugin — Claude Code hoy: `general-purpose` con task prompt explícito.

El subagent corre en fork real; la skill recibe el summary al tool result y lo folds en su output — no paste-through.

**Plugin agent primitive (entregado en F2)**: `agents/<slug>.md` con frontmatter `{name, description, tools, model}`. **Shape distinto al skill primitive**: `tools` es comma-separated string (oficial Claude Code subagent format), no YAML list `allowed-tools`. Sin campos inventados. Namespace `pos-*` obligatorio. Contract tests en `agents/tests/test_agent_frontmatter.py` parametrizados por `ALLOWED_AGENTS`. No hay `agents_allowed` en `policy.yaml` hoy (sin enforcement consumer; el Stop hook lee `skills.jsonl`, no `agents.jsonl`).

**Precedentes**:

- `branch-plan` (E1b) delega cuando el plan es heavy (pick `Plan` / `code-architect` / `Explore` built-in por capacidad).
- `deep-interview` (E1b) nunca delega — su coste está en el dialog, no en reading.
- `pre-commit-review` (E2a) delega siempre a `pos-code-reviewer` como hybrid pattern (main prepara context, subagent analiza, main folds) — **primera consumidora del plugin agent post-F2** (antes de F2 apuntaba a `code-reviewer` built-in).
- `compound` (E3a) delega a `pos-architect` post-merge para pattern extraction — **primera consumidora del plugin agent post-F2** (antes de F2 apuntaba a `code-architect` built-in).
- `project-kickoff` y `writing-handoff` (E1a), `simplify` (E2a) son main-strict por scope acotado. `pattern-audit` (E3a) y `audit-session` (F1) son main-strict por design — **forward-compat negación**: nunca deben referenciar plugin subagents (negation list de tests incluye `pos-architect` / `pos-code-reviewer` desde F2).

**Precedentes de writer-scope**: `writing-handoff` (E1a) escribe **sólo** en HANDOFF.md con scope por sección declarado en el body; `simplify` (E2a) es la **segunda** writer-scoped del repo — edita **sólo** archivos presentes en `git diff --name-only main..HEAD`, con scope check en cada `Edit` call y reclasificación a `skip (out of scope)` si el `file_path` no está en la lista derivada. Ambas cierran con reporte de qué cambiaron y qué decidieron no tocar.

## Modelo

El primitive no soporta `model:` en el frontmatter — la skill corre en el modelo del orchestrator (usuario). El bloque `model_routing` en `policy.yaml` es **advisory/documental**, no enforcement. La columna "Modelo" en [skills-map.md](skills-map.md) refleja la recomendación histórica por skill; no es contrato.

## Tests

- **Contract tests** del primitive en `.claude/skills/tests/test_skill_frontmatter.py` — parametrizados por `ALLOWED_SKILLS` (renombrado desde `E1_SKILLS_KNOWN` en E2a cuando la allowlist cruzó el límite de fase; contract-bound al `skills_allowed` del meta-repo, no era-bound: extender = añadir entrada aquí + en `policy.yaml`, no renombrar). Validan: dir + SKILL.md existe; NO `skill.json`; frontmatter keys ⊆ `{name, description, allowed-tools}`; `name` == dir name; description case-insensitive `startswith "use when"`; `allowed-tools` es `list[str]` si presente; `name` sin prefijo `pos:`; body referencia `.claude/skills/_shared/log-invocation.sh`; shared logger existe y es ejecutable.
- **Behavior tests** del body — añadir una `TestXxxBehavior` class por skill cuando el framing del body sea parte del contrato. Existentes: `TestBranchPlanBehavior` + `TestDeepInterviewBehavior` (E1b — disclaim de marker, opt-in gating, no silent mutation); `TestPreCommitReviewBehavior` + `TestSimplifyBehavior` (E2a — delegation a `pos-code-reviewer` post-F2, scope `git diff main...HEAD`, disclaim de escritura / reemplazo de `simplify`, writer-scoped-al-diff, reducer-not-bug-finder, reporte de qué simplificó + qué decidió no tocar); `TestCompoundBehavior` (E3a, flippeada en F2 — delegation a `pos-architect` con fallback `general-purpose`); negation lists de `TestPatternAuditBehavior` (E3a) y `TestAuditSessionBehavior` (F1) extendidas con `pos-*` desde F2 (forward-compat: main-strict skills nunca referencian plugin subagents).
- **Integration contract** logger ↔ Stop hook en `hooks/tests/test_skills_log_contract.py`. Añadir un caso `test_all_N_skills_end_to_end` (o renombrar el existente) cuando la allowlist crezca. Precedente: `test_all_four_e1_skills_end_to_end` (E1b) → `test_all_six_e1_e2a_skills_end_to_end` (E2a).

## Logging — best-effort via helper

Toda skill termina su body con una invocación Bash a `.claude/skills/_shared/log-invocation.sh <name> <status>`:

```bash
.claude/skills/_shared/log-invocation.sh <name> ok
```

- `<name>` — el slug de la skill (sin prefijo `pos:`).
- `<status>` — `ok` (default), `partial`, `declined`, `ambiguous`, `degraded`, `slug_conflict` según corresponda al camino recorrido.

El helper emite una línea JSONL a `.claude/logs/skills.jsonl` con shape estable `{ts, skill, session_id, status}`. Fallback `session_id: "unknown"` si `CLAUDE_SESSION_ID` ausente; `mkdir -p` del directorio de logs.

**Best-effort operacional**: si el modelo omite el step, el sistema pierde traza de esa invocación, pero **nunca rompe**. `stop-policy-check.py` trata ausencia de entrada como "no invocación" → allow (silencio ≠ violación). Extender el shape a 5+ campos requiere nueva rama + migración del extractor + tests del contrato.

## Allowlist enforcement

`policy.yaml.skills_allowed` debe listar cada skill que el repo acepta invocar. Ausencia = `stop-policy-check.py` pasa en modo `deferred` (scaffold sin enforcement). Lista poblada = enforcement live: invocación logged para la sesión actual que no esté en la allowlist deniega Stop. Lista `[]` = deny-all explícito. Formato mal formado (escalar / lista con no-strings / dict) = `SKILLS_ALLOWED_INVALID` → pass-through con `status: policy_misconfigured` observable (no silencioso).

Ver `hooks/_lib/policy.py::skills_allowed_list` + `.claude/rules/hooks.md § Séptimo hook` para el contrato tri-estado completo.

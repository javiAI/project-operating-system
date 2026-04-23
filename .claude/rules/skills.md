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

La skill debe escoger el `subagent_type` **por capacidad**, no por nombre hardcoded — los nombres concretos son defaults de Claude Code y pueden variar entre releases/entornos. Regla operativa: inspeccionar el enum `subagent_type` de la tool `Agent` en runtime y matchear por capacidad. Los nombres abajo reflejan los defaults de Claude Code hoy:

- **Planning independiente** (cross-check contra el plan de la skill) — Claude Code hoy: `Plan`.
- **Segunda opinión arquitectónica** (crítica de diseño) — Claude Code hoy: `code-architect`.
- **Context gathering cross-files** (explora y devuelve digest) — Claude Code hoy: `Explore`.
- **Review de diff de rama** (confidence-filtered review) — Claude Code hoy: `code-reviewer` (patrón canónico previsto para `/pos:pre-commit-review` en E2a).
- **Fallback general** si ninguna capacidad específica encaja — Claude Code hoy: `general-purpose` con task prompt explícito.

El subagent corre en fork real; la skill recibe el summary al tool result y lo folds en su output — no paste-through.

**Precedentes**: `branch-plan` (E1b) delega cuando el plan es heavy; `deep-interview` (E1b) nunca delega (su coste está en el dialog, no en reading); `project-kickoff` y `writing-handoff` (E1a) son main-strict por scope acotado.

## Modelo

El primitive no soporta `model:` en el frontmatter — la skill corre en el modelo del orchestrator (usuario). El bloque `model_routing` en `policy.yaml` es **advisory/documental**, no enforcement. La columna "Modelo" en [skills-map.md](skills-map.md) refleja la recomendación histórica por skill; no es contrato.

## Tests

- **Contract tests** del primitive en `.claude/skills/tests/test_skill_frontmatter.py` — parametrizados por `E1_SKILLS_KNOWN` (contract-bound al `skills_allowed` del meta-repo, no era-bound). Validan: dir + SKILL.md existe; NO `skill.json`; frontmatter keys ⊆ `{name, description, allowed-tools}`; `name` == dir name; description case-insensitive `startswith "use when"`; `allowed-tools` es `list[str]` si presente; `name` sin prefijo `pos:`; body referencia `.claude/skills/_shared/log-invocation.sh`; shared logger existe y es ejecutable.
- **Behavior tests** del body — ver `TestBranchPlanBehavior` + `TestDeepInterviewBehavior` en el mismo file (añadidas en E1b). Lock down framing strings concretos (disclaim de marker, opt-in gating, no silent mutation). Modelo: añade una `TestXxxBehavior` class por skill cuando el framing del body sea parte del contrato.
- **Integration contract** logger ↔ Stop hook en `hooks/tests/test_skills_log_contract.py`. Añadir un caso `test_all_N_skills_end_to_end` cuando la allowlist crezca (precedente: `test_all_four_e1_skills_end_to_end` en E1b).

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

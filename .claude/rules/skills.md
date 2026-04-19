---
name: skills
description: Reglas cuando editas skills del plugin pos
paths:
  - "skills/**"
---

# Reglas — Skills del plugin `pos`

## Estructura

Cada skill vive en `skills/<nombre>/`:

```
skills/<nombre>/
├── skill.md          # frontmatter + cuerpo
├── scripts/          # opcional — scripts invocados via !`...`
└── tests/            # tests del comportamiento
```

## Frontmatter obligatorio

```yaml
---
name: pos:<nombre>
description: "<verbo + qué hace + cuándo invocarla>"
user-invocable: true
disable-model-invocation: false
allowed-tools: [Read, Grep, Bash, Write, Edit]
model: claude-sonnet-4-6   # ver model-routing en policy.yaml
effort: medium             # low | medium | high
context: fork              # si la skill no debe contaminar contexto principal
agent: code-reviewer       # obligatorio si context: fork
hooks:
  - PreToolUse
paths: []                  # scope opcional — skill sólo disponible bajo esos paths
---
```

## Criterios `context: fork`

Usa `context: fork` + `agent:` cuando:
- La skill lee ≥3 archivos grandes (research, logs, diffs completos).
- La skill emite ≥2k tokens de análisis intermedio.
- La skill corre `/pos:compound`, `/pos:audit-*`, `/pos:pre-commit-review`, `/pos:simplify`.

**No** uses `context: fork` para skills rápidas de escritura (ej. `/pos:kickoff`, `/pos:handoff-write`) — el fork añade latencia y rompe interactividad.

## Modelo

- `claude-haiku-4-5-20251001` — lookups, compresión, extracción simple.
- `claude-sonnet-4-6` — default: review, generación, planning.
- `claude-opus-4-7` — SÓLO: arquitectura (`/pos:branch-plan`, `/pos:deep-interview`), refactors cross-módulo, debugging complejo.

Declarar el modelo en frontmatter; `policy.yaml` valida el uso.

## Sustituciones

- `$ARGUMENTS` — args completos.
- `$1`, `$2`, ... — posicionales.
- `${CLAUDE_SESSION_ID}` — ID sesión.
- `${CLAUDE_SKILL_DIR}` — dir de la skill.
- `` !`comando` `` — inyecta stdout en línea (shell: true en frontmatter si aplica).

## Tests

- Skills con lógica no trivial: test con `claude -p "/pos:<nombre> <args>"` en subprocess + snapshot del output.
- Skills de pura orquestación (plantillas de prompt): smoke test que valida parseo del frontmatter.

## Logging

Toda invocación escribe a `.claude/logs/skills.jsonl` vía hook `PreToolUse` + `Stop`. La skill no debe loguear por sí misma.

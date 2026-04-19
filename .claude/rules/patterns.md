---
name: patterns
description: Reglas al editar registros de patrones extraídos por compound + invariants
paths:
  - ".claude/patterns/**"
  - ".claude/invariants/**"
  - ".claude/anti-patterns/**"
---

# Reglas — Patterns registry

## Origen

Los patrones no se escriben a mano al inicio. Emergen:

1. `/pos:compound` (post-merge, con trigger por `touched_paths` del profile) analiza el diff.
2. Detecta repeticiones cross-rama con evidencia (≥2 commits distintos con estructura similar).
3. Emite PR separado `chore/compound-YYYY-MM-DD` con:
   - Nuevo archivo `.claude/patterns/<area>/<nombre>.md`.
   - Evidencia: enlaces a commits + diffs minimales.
   - Propuesta de antipattern counterpart si aplicable.

## Formato de un pattern file

```markdown
---
name: <nombre-kebab>
description: <qué resuelve, 1 línea>
paths:
  - "src/app/api/**"
evidence:
  - commit: <sha>
    diff_range: "path/a.ts:12-48"
  - commit: <sha>
    diff_range: "path/b.ts:20-55"
introduced_in: <branch-name>
supersedes: []     # otros patterns que reemplaza
conflicts_with: [] # patterns que NO pueden coexistir
---

# <Nombre humano>

## Cuándo aplicar
<condición>

## Implementación canónica
```ts
// ejemplo mínimo reproducible
```

## Antipattern (qué NO hacer)
<explicación + ejemplo>

## Excepciones justificadas
<cuándo saltarse la regla con waiver>
```

## Antipatterns

En `.claude/anti-patterns/common.md`. Formato similar pero declarativo (lo que está prohibido + por qué). Hook `PreToolUse(Write)` grepea y bloquea si detecta match sin waiver.

## Invariants

`.claude/invariants/INVARIANTS.md` — contratos cross-módulo. Formato:

```markdown
## <nombre del invariante>

**Scope**: <qué módulos/archivos afecta>
**Precondition**: <qué debe ser cierto antes>
**Postcondition**: <qué debe ser cierto después>
**Enforcement**: <qué hook o test lo valida>
**Origin**: <branch o issue donde se estableció>
```

Un invariante roto bloquea merge (hook `pre-pr-gate.sh` lo valida con script declarado en `enforcement`).

## Reglas duras

1. **No editar pattern files a mano** salvo para actualizar `evidence`/`supersedes` con nuevo commit. Nuevos patrones → `/pos:compound`.
2. **Paths obligatorio** — sin `paths:` no se inyecta; un pattern global es casi siempre un smell (pon la regla en `CLAUDE.md` o `rules/`).
3. **Un pattern, una cosa**. Si el archivo crece >200 líneas, se parte.
4. **Conflict resolution**: si dos patterns aplican al mismo archivo y conflictan, hook `InstructionsLoaded` emite warning al arranque de sesión y fuerza que uno sea `supersedes` del otro.

## Purga

Patterns que no se referencian en commits durante ≥6 meses son candidatos de purga. `/pos:audit-session --patterns` lo reporta.

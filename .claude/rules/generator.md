---
name: generator
description: Reglas cuando editas el generador TypeScript (tsx) que produce proyectos a partir de profiles
paths:
  - "generator/**"
  - "templates/**"
  - "questionnaire/**"
---

# Reglas — Generador

## Stack

- TypeScript con `tsx` (cero build). Módulos ES.
- Handlebars (`handlebars`) para templates; registrar helpers en `generator/lib/handlebars-helpers.ts`.
- Validación de schema con `zod`. Nada de `any`.
- Lectura/escritura de archivos con `node:fs/promises`.
- YAML con `yaml` package (no `js-yaml`).

## Estructura obligatoria

```
generator/
├── run.ts                  # entrypoint CLI (args: --profile, --out, --dry-run)
├── lib/
│   ├── schema.ts           # zod schemas del profile
│   ├── validators.ts       # validaciones cross-field
│   ├── token-budget.ts     # checker de presupuesto
│   └── handlebars-helpers.ts
└── renderers/
    ├── claude-md.ts
    ├── master-plan.ts
    ├── roadmap.ts
    ├── handoff.ts
    ├── agents.ts
    ├── policy.ts
    ├── rules.ts            # renderiza .claude/rules/*.md
    ├── hooks.ts            # copia hooks + customiza paths
    ├── skills.ts           # copia skills
    ├── ci-cd.ts            # genera .github/workflows/*.yml
    └── tests.ts            # genera test harness según stack
```

Cada renderer exporta una función pura `render(profile: Profile): FileWrite[]`.

## Tests

- Vitest. Test file pair obligatorio para cada archivo en `generator/lib/**` y `generator/renderers/**`.
- Snapshot testing para outputs deterministas de renderers.
- Fixtures en `generator/__fixtures__/profiles/` (uno por profile predefinido).
- Tests de integración: generar proyecto completo en `tmp/` y validar estructura.

## Errores

- Profile inválido → error descriptivo con ruta del campo + sugerencia. Exit code 1.
- Template missing → fail-fast con path completo esperado. Exit code 2.
- Output dir no vacío sin `--force` → abort. Exit code 3.

## Determinismo del output

Los renderers deben producir **byte-identical output** para el mismo profile. Sin `Date.now()`, sin `Math.random()`, sin paths absolutos del host. Usar `profile.metadata.generatedAt` inyectado desde afuera para timestamps.

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

## Profiles (entregado en B2)

- **Location**: `questionnaire/profiles/<slug>.yaml`. Canonical source. El generador los lee desde aquí.
- **Shape**: `{ version, profile: { name, description }, answers: { "<path.dotted>": <value> } }`. Claves dotted alineadas con `field.path` del schema. Top-level strict (no extra keys).
- **Parcialidad**: un profile no tiene que cubrir todos los `required` del project_profile final. Los 3 campos user-specific (`identity.name`, `identity.description`, `identity.owner`) quedan fuera por diseño.
- **Validator**: `npx tsx tools/validate-profile.ts <path>` — emite issues de 5 kinds (ver [docs/ARCHITECTURE.md §2 Profiles](../../docs/ARCHITECTURE.md)). CI corre un step `Validate profiles` sobre los 3 canónicos.
- **Fixtures**: `tools/__fixtures__/profiles/{valid,invalid}/*.yaml`. Los `valid/` son duplicados literales de los canónicos (simplicidad; consolidar si B3 revela mejor mecanismo).
- **Añadir un nuevo profile**: crear YAML en `questionnaire/profiles/`, duplicarlo en `tools/__fixtures__/profiles/valid/`, añadir invocación al script `validate:profiles` de `package.json`. Tests unitarios no necesitan cambio (reutilizan el schema base).

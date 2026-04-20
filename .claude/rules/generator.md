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

## Runner (entregado en B3)

- **Entrypoint**: [generator/run.ts](../../generator/run.ts). CLI con `--profile <path>` (requerido) y `--validate-only` (boolean). Schema hard-coded a `questionnaire/schema.yaml` (flag `--schema` diferido).
- **Exports testables**: `runValidation(profilePath): Promise<RunResult>` + `formatReport(result, profilePath): string`. `main()` es wrapper con `/* v8 ignore start/stop */`.
- **Semántica exit codes**:
  - `0` — profile sin issues ni completeness-errors. Las 3 warnings user-specific (`identity.name|description|owner`) son OK por diseño (se resuelven en runner interactivo de fase posterior).
  - `1` — `validateProfile` emite issues O `completenessCheck` emite errors (required no-user-specific faltante).
  - `2` — archivo ausente, YAML ilegible, args inválidos, o flag diferido (`--out` / `--dry-run`).
- **Flags diferidos a C1**: `--out` y `--dry-run` se declaran en `parseArgs` (para que `strict: true` no las rechace como "unknown") pero el runner las rechaza explícitamente con mensaje `flag --X not supported in B3; planned for C1` + exit 2.
- **Fixtures de integración**: [generator/__fixtures__/profiles/{valid-partial,missing-required,invalid-value}/](../../generator/__fixtures__/profiles/) — uno por clase de outcome (exit 0 con warnings / exit 1 completeness / exit 1 value).
- **Smoke CI**: script `npm run validate:generator` corre el runner sobre los 3 profiles canónicos; step homónimo en [.github/workflows/ci.yml](../../.github/workflows/ci.yml) detecta regresiones antes de los unit tests.

## Deferrals (B3)

- **`generator/lib/token-budget.ts`** — **diferido**. Motivo: `questionnaire/schema.yaml` no declara `workflow.token_budget` todavía; implementar el checker sin campo que leer sería abstracción prematura (CLAUDE.md regla #7). Reintroducir en rama posterior cuando el schema añada el campo. No crear el archivo hasta entonces.
- **`--schema` flag** — diferido. Mientras haya un único schema canónico, hard-coded basta. Abrir cuando aparezca un 2º schema (por ejemplo, variante Python-only).
- **`--out` y `--dry-run`** — diferidos a C1 (rama `feat/c1-renderers-core-docs`) cuando existan renderers y output de archivos.

## Reuso desde `tools/lib/` (pattern-before-abstraction, 3ª aplicación)

Norma: antes de duplicar código en `generator/lib/`, re-exportar de `tools/lib/`. Bifurcar sólo cuando aparezca lógica generator-only que no tiene sentido en `tools/`.

- `generator/lib/schema.ts` re-exporta `parseSchemaFile`, `parseProfileFile`, `validateProfile` + tipos (`ProfileFile`, `ProfileIssue`, `ProfileIssueKind`, `SchemaFile`) desde `tools/lib/meta-schema.ts` + `tools/lib/profile-validator.ts`. **Cero lógica propia.** Si en el futuro hace falta una función generator-only, añadirla al mismo archivo sin romper los re-exports.
- `generator/lib/profile-loader.ts` reutiliza `readAndParseYaml` + `errorMessage` de [tools/lib/read-yaml.ts](../../tools/lib/read-yaml.ts) (2ª aplicación, entregada en B2).
- `generator/lib/validators.ts` consume el tipo `SchemaFile` reexportado y no importa zod directamente.

Historial de aplicaciones:

1. **1ª (B1)** — [tools/lib/condition-parser.ts](../../tools/lib/condition-parser.ts) comparte interfaz con `tools/lib/cross-validate.ts` sin abstraer prematuramente.
2. **2ª (B2)** — extracción de `tools/lib/read-yaml.ts` tras 2 call-sites (validate-profile + validate-questionnaire).
3. **3ª (B3)** — re-exports `generator/lib/schema.ts` + reuso read-yaml desde `generator/lib/profile-loader.ts`.

Si aparece una 4ª aplicación que exija lógica generator-only (p.ej. validación cross-field usando templates Handlebars), bifurcar entonces.

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
├── run.ts                  # entrypoint CLI (--profile, --validate-only, --dry-run, --out)
├── lib/
│   ├── schema.ts           # re-export zod schemas (desde tools/lib/)
│   ├── validators.ts       # completenessCheck + USER_SPECIFIC_PATHS
│   ├── profile-loader.ts   # readAndParseYaml-backed loader
│   ├── profile-model.ts    # buildProfile: dotted → nested + placeholders
│   ├── render-pipeline.ts  # renderAll + writeFiles + isDirEmpty + FileWrite
│   ├── handlebars-helpers.ts
│   ├── template-loader.ts  # Handlebars.create() + registerHelpers + compile
│   ├── token-budget.ts     # [diferido] checker de presupuesto
│   └── __tests__/          # test pairs
└── renderers/
    ├── index.ts            # tuple congelada coreDocRenderers
    ├── claude-md.ts        # C1
    ├── master-plan.ts      # C1
    ├── roadmap.ts          # C1
    ├── handoff.ts          # C1
    ├── agents.ts           # C1
    ├── readme.ts           # C1
    ├── policy.ts           # C2 (pendiente)
    ├── rules.ts            # C2 (pendiente) — .claude/rules/*.md
    ├── tests.ts            # C3 (pendiente) — test harness según stack
    ├── ci-cd.ts            # C4 (pendiente) — .github/workflows/*.yml
    ├── hooks.ts            # C5 (pendiente) — copia + customiza paths
    └── skills.ts           # C5 (pendiente) — copia skills
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
- **Semántica exit codes** (ampliada en C1):
  - `0` — profile sin issues ni completeness-errors. Las 3 warnings user-specific (`identity.name|description|owner`) son OK por diseño (se resuelven en runner interactivo de fase posterior).
  - `1` — `validateProfile` emite issues O `completenessCheck` emite errors (required no-user-specific faltante). `--dry-run`/`--out` cortan antes de render.
  - `2` — archivo ausente, YAML ilegible, args inválidos, modos mutuamente exclusivos combinados.
  - `3` — `--out <dir>` target no vacío (C1; protege output del usuario, `--force` fuera de scope).
- **CLI modes (C1)**: `--validate-only` / `--dry-run` / `--out <dir>` son mutuamente exclusivos. Sin flags = `--validate-only` (compat con B3).
- **Fixtures de integración**: [generator/__fixtures__/profiles/{valid-partial,missing-required,invalid-value}/](../../generator/__fixtures__/profiles/) — uno por clase de outcome (exit 0 con warnings / exit 1 completeness / exit 1 value).
- **Smoke CI**: script `npm run validate:generator` corre el runner sobre los 3 profiles canónicos; step homónimo en [.github/workflows/ci.yml](../../.github/workflows/ci.yml) detecta regresiones antes de los unit tests.

## Renderers (entregado en C1)

- **Pipeline**: [generator/lib/render-pipeline.ts](../../generator/lib/render-pipeline.ts). `renderAll(profile, renderers)` concatena `FileWrite[]` y **falla por invariante** ante colisión de paths (incluye índices de los dos renderers que colisionan). `writeFiles(dir, files)` crea subdirs (`mkdir -p`). `isDirEmpty(dir)` gate pre-`--out`.
- **`FileWrite` shape**: `{ path: string; content: string }`. `path` relativo al root del repo generado (subdirs permitidos). Sin `mode` en C1 — se añade en C5 si hooks ejecutables lo requieren.
- **Renderer contract**: función pura `(profile: Profile) => FileWrite[]`. Sin `Date.now()`, sin `Math.random()`, sin env vars. Byte-identical entre runs (tests lo validan con `JSON.stringify` comparativo).
- **Core docs (C1)**: 6 renderers (`claude-md`, `master-plan`, `roadmap`, `handoff`, `agents`, `readme`) expuestos como tuple congelada `coreDocRenderers` en [generator/renderers/index.ts](../../generator/renderers/index.ts). Añadir un 7º = crear renderer + registrarlo en el array adecuado.
- **Templates**: Handlebars en `templates/*.hbs` cargados sincronamente al eval del módulo renderer vía [generator/lib/template-loader.ts](../../generator/lib/template-loader.ts) (4ª aplicación pattern-before-abstraction: evita duplicar `Handlebars.create() + registerHelpers + compile` en cada renderer).
- **Helpers**: [generator/lib/handlebars-helpers.ts](../../generator/lib/handlebars-helpers.ts) — `eq`, `neq`, `includes`, `kebabCase`, `upperFirst`, `jsonStringify`. Registrados sobre instancia privada. Ampliar aquí si un nuevo template lo exige, con tests de compilación real.
- **Profile model**: [generator/lib/profile-model.ts](../../generator/lib/profile-model.ts) — `buildProfile(file)` expande dotted-answers a objeto nested e inyecta `TODO(identity.X)` para los 3 paths user-specific faltantes (`identity.name|description|owner`). Los templates referencian `{{answers.identity.name}}` sin `{{#if}}` guards.
- **CLI modes**: `--validate-only` (default), `--dry-run`, `--out <dir>` — mutuamente exclusivos. `--out` sobre dir no vacío → exit 3. Validación fallida (exit 1) corta antes del render. Ver [docs/ARCHITECTURE.md § 3 Entrypoint](../../docs/ARCHITECTURE.md).
- **Snapshots**: `generator/__snapshots__/<profile-slug>/<path>.snap` (3 profiles × 6 templates = 18 en C1). Añadir template = revisar 3 nuevos diffs pre-commit.
- **CI smoke**: scripts `validate:generator` (exit 0 sobre 3 canonicals) + `render:generator` (dry-run sobre 3 canonicals); ambos son steps en [.github/workflows/ci.yml](../../.github/workflows/ci.yml).

## Deferrals (B3 / C1)

- **`generator/lib/token-budget.ts`** — **diferido**. Motivo: `questionnaire/schema.yaml` no declara `workflow.token_budget` todavía; implementar el checker sin campo que leer sería abstracción prematura (CLAUDE.md regla #7). Reintroducir en rama posterior cuando el schema añada el campo. No crear el archivo hasta entonces.
- **`--schema` flag** — diferido. Mientras haya un único schema canónico, hard-coded basta. Abrir cuando aparezca un 2º schema (por ejemplo, variante Python-only).
- **`--force` flag** — fuera de scope C1. `--out` sobre dir no vacío aborta con exit 3 protegiendo output del usuario. Reabrir cuando un flujo legítimo lo exija.
- **`templates/.claude/rules/docs.md.hbs`** — diferido a C2 (coherencia de scope con `.claude/rules/*.md`). Completa el carry-over Fase N+7 iniciado en C1.

## Reuso desde `tools/lib/` (pattern-before-abstraction, 4ª aplicación)

Norma: antes de duplicar código, extraer helper compartido sólo cuando haya ≥2 call-sites reales. Bifurcar solo cuando aparezca lógica específica-de-dominio que no tiene sentido en el módulo común.

- `generator/lib/schema.ts` re-exporta `parseSchemaFile`, `parseProfileFile`, `validateProfile` + tipos (`ProfileFile`, `ProfileIssue`, `ProfileIssueKind`, `SchemaFile`) desde `tools/lib/meta-schema.ts` + `tools/lib/profile-validator.ts`. **Cero lógica propia.** Si en el futuro hace falta una función generator-only, añadirla al mismo archivo sin romper los re-exports.
- `generator/lib/profile-loader.ts` reutiliza `readAndParseYaml` + `errorMessage` de [tools/lib/read-yaml.ts](../../tools/lib/read-yaml.ts) (2ª aplicación, entregada en B2).
- `generator/lib/validators.ts` consume el tipo `SchemaFile` reexportado y no importa zod directamente.
- `generator/lib/template-loader.ts` centraliza `Handlebars.create() + registerHelpers + compile` tras la 2ª aparición del triple (6 renderers habrían duplicado la misma secuencia).

Historial de aplicaciones:

1. **1ª (B1)** — [tools/lib/condition-parser.ts](../../tools/lib/condition-parser.ts) comparte interfaz con `tools/lib/cross-validate.ts` sin abstraer prematuramente.
2. **2ª (B2)** — extracción de `tools/lib/read-yaml.ts` tras 2 call-sites (validate-profile + validate-questionnaire).
3. **3ª (B3)** — re-exports `generator/lib/schema.ts` + reuso read-yaml desde `generator/lib/profile-loader.ts`.
4. **4ª (C1)** — `generator/lib/template-loader.ts` tras la 2ª replicación del triple `create + registerHelpers + compile`.

Si aparece una 5ª aplicación que exija lógica específica (p.ej. loader que además valide estructura del template), bifurcar entonces.

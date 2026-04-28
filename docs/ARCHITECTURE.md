# ARCHITECTURE — project-operating-system

> Decisiones canónicas. Evoluciona con cada fase mayor. Si un archivo en el repo contradice esto, este documento gana.

## 1. Modelo de dos capas

```
┌────────────────────────────────────────┐
│  META-REPO (este repo, plugin "pos")   │   control plane
│  - cuestionario                        │
│  - generador TypeScript                │
│  - templates Handlebars                │
│  - skills (context: fork)              │
│  - hooks (Python)                      │
│  - policy.yaml canónico                │
└───────────────┬────────────────────────┘
                │ genera
                ▼
┌────────────────────────────────────────┐
│  REPO GENERADO                         │   runtime plane
│  - copia de skills/hooks/agents        │
│  - CLAUDE.md + rules adaptadas         │
│  - CI/CD workflows                     │
│  - test harness                        │
│  - policy.yaml propia                  │
└────────────────────────────────────────┘
```

El meta-repo nunca ejecuta código del proyecto destino. El proyecto destino nunca depende del meta-repo en runtime (todo se copia).

### 1.1. Knowledge plane (opcional)

> **Opcional.** Capa extra mountable *dentro* del repo generado, adoptable vía opt-in del questionnaire.
> Contrato fijado en G1 — ver especificación completa en [docs/KNOWLEDGE_PLANE.md](KNOWLEDGE_PLANE.md).
> Renderer y esqueleto `vault/` en G2 (no implementados todavía).

```
┌────────────────────────────────────────┐
│  META-REPO (control plane)             │
└───────────────┬────────────────────────┘
                │ genera
                ▼
┌────────────────────────────────────────┐
│  REPO GENERADO (runtime plane)         │
│                                        │
│  [opt-in] vault/ (knowledge plane):    │
│    raw/        fuentes inmutables      │
│    wiki/        síntesis               │
│    config.md   configuración           │
└────────────────────────────────────────┘
```

**Tres capas** (terminología del [gist de Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)):
`vault/raw/` (fuentes) · `vault/wiki/` (síntesis) · `vault/config.md` (configuración de instancia).

**Principios**: file-based · tool-agnostic · opt-in (`integrations.knowledge_plane.enabled: boolean, default false`) · sin runtime compartido.

Obsidian + Web Clipper = primer reference adapter previsto (G2), no contrato base.

## 2. Cuestionario → profile → generación

### Flujo

```
1. Usuario invoca "pos init" o skill `/pos:kickoff --bootstrap`.
2. Cuestionario interactivo (o profile predefinido + overrides).
3. Respuestas validadas contra `questionnaire/schema.yaml` (zod en runtime).
4. Output: `project_profile.yaml` en el dir destino.
5. Generador toma `project_profile.yaml` + `templates/` → produce repo completo.
6. Post-generación: `git init`, primer commit, opcional push.
```

### Categorías del cuestionario (A-G)

- **A. Identidad**: nombre, descripción, licencia, owner.
- **B. Dominio**: tipo de proyecto (web app, CLI, agent SDK, library, etc.).
- **C. Stack**: lenguajes, frameworks, DB, infra. Profiles pre-cocinan 60%.
- **D. Testing**: unit/integration/e2e frameworks, coverage threshold.
- **E. Integraciones**: qué MCPs opt-in (MemPalace, NotebookLM, etc.), otros servicios.
- **F. Workflow**: CI host, branch protection, release strategy, token budget.
- **G. Claude Code**: modelo default, skills extra, equipo/solo.

### Profiles predefinidos (entregado en B2)

- `nextjs-app` — Next.js 15 + Prisma + PostgreSQL + Vitest + Playwright.
- `agent-sdk` — Agent SDK + Python + pytest + uv.
- `cli-tool` — TypeScript CLI + oclif + vitest.

Extensible en `questionnaire/profiles/*.yaml`. El generador soporta override key-por-key.

**Shape canonical** (validado por [tools/lib/profile-validator.ts](../tools/lib/profile-validator.ts)):

```yaml
version: "0.1.0"
profile:
  name: <slug>
  description: <one-liner>
answers:
  "<path.dotted>": <value>
```

Claves dotted (`"stack.language": "typescript"`) alineadas 1:1 con `field.path` del schema. Facilita override key-por-key en el runner (B3) y evita ambigüedades al renombrar fields.

**Profiles son parciales por diseño.** No tienen que cubrir todos los `required` del project_profile final. Los 3 campos user-specific (`identity.name`, `identity.description`, `identity.owner`) quedan **fuera** de los profiles y se resuelven en el runner interactivo. El validator sólo verifica que los paths declarados existan en el schema y que sus valores respeten los constraints del field.

**Validaciones del profile validator** ([tools/lib/profile-validator.ts](../tools/lib/profile-validator.ts)):

- `answer-unknown-path` — path declarado en `answers` no existe en el schema.
- `answer-type-mismatch` — tipo del valor no coincide con `field.type` (string/number/boolean/array).
- `answer-value-not-in-enum` — valor de enum fuera de `field.values`.
- `answer-array-item-type-mismatch` — un elemento del array no coincide con `field.items`.
- `answer-constraint-violation` — `pattern` / `minLength` / `maxLength` / `min` / `max` / `minItems` / `maxItems` violado.

**Brecha conocida** (decisión B2): el check `answer-value-not-in-array-allowlist` no se implementa todavía. `ArrayField.values` existe en el schema (ver `integrations.mcps`) pero la validación a nivel de instancia se difiere — ampliar en una rama posterior cuando el tema se reabra.

**Validador CLI**: `npx tsx tools/validate-profile.ts <profile.yaml> [--schema ...]` — exit 0 (OK), 1 (issues), 2 (YAML ilegible / archivo ausente / falta arg). Corre en CI (step `Validate profiles`, matrix ubuntu+macos, node 20).

### Schema DSL (entregado en B1)

El schema NO es JSON Schema. Es un DSL propio YAML declarativo, validado por [tools/lib/meta-schema.ts](../tools/lib/meta-schema.ts) usando zod.

**Razones para DSL propio**:

- Permite verificar coherencia cross-file (`questions[].maps_to` ↔ paths de `schema.yaml`) sin ecosistema externo.
- Más legible al editar a mano: secciones A-G con `fields[]` discriminados por `type` (`string | number | boolean | enum | array`), constraints inline (`required`, `default`, `pattern`, `min/max`, `values`).
- `array` fields aceptan `items` (primitivo) y `values:` opcional (allowlist) para restringir elementos permitidos, simétrico con `enum.values`. `default` debe ser coherente con `items`, respetar `minItems/maxItems` y, si hay `values`, estar contenido en el allowlist.
- Sin deps pesadas: solo `zod` + `yaml`.

**Condiciones en `questions[].when:`** — subset mínimo parseado por [tools/lib/condition-parser.ts](../tools/lib/condition-parser.ts):

- Operandos: path dotted (`stack.language`), literales (string, number, bool, null), array literal (`['a', 'b']`).
- Operadores: `==`, `!=`, `in`, `&&`, `||`, `!`, paréntesis.
- Evaluable sobre el profile parcial durante el runner interactivo (B3).

**Validaciones semánticas cross-file** ([tools/lib/cross-validate.ts](../tools/lib/cross-validate.ts)):

- `maps_to-unknown-path` — `questions[].maps_to` apunta a un path no declarado en el schema.
- `required-uncovered` — field `required: true` sin pregunta y sin `default`.
- `section-unknown` — `questions[].section` no existe en el schema.
- `option-outside-enum` — opción de `single`/`multi` fuera de los `values` del enum.
- `question-field-type-mismatch` — `question.type` incompatible con `field.type` (`text→string`, `number→number`, `bool→boolean`, `single→enum`, `multi→array`).
- `question-section-mismatch` — la pregunta vive en una sección distinta a la del field al que apunta.
- `when-unknown-path` — expresión `when:` referencia un path no declarado en el schema.

**Validador CLI**: `npx tsx tools/validate-questionnaire.ts` — exit 0 (ok), 1 (issues estructurales o meta-schema), 2 (YAML ilegible o archivo ausente). Corre en CI matrix (ubuntu+macos, node 20).

## 3. Generador (TypeScript + tsx)

### Entrypoint (entregado en B3, ampliado en C1)

[generator/run.ts](../generator/run.ts) es el CLI del runner. B3 entregó el runner de validación; C1 añade render + escritura.

**Signatures públicas** (usables desde tests y, en el futuro, desde skills):

```ts
// generator/run.ts
export type Mode = "validate-only" | "dry-run" | "write";
export type RunResult = {
  ok: boolean;
  issues: ProfileIssue[];                 // de profile-validator
  errors: CompletenessEntry[];            // required-missing (non-user-specific)
  warnings: CompletenessEntry[];          // required-missing (user-specific)
  parseErrors: string[];                  // YAML ilegible, schema roto, etc.
  exitCode: 0 | 1 | 2 | 3;
};

export async function runValidation(profilePath: string): Promise<RunResult>;
export async function runRender(profilePath: string): Promise<
  | { ok: true; files: FileWrite[]; warnings: CompletenessEntry[] }
  | { ok: false; error: string }
>;
export function formatReport(result: RunResult, profilePath: string): string;
export function formatRenderSummary(
  files: FileWrite[],
  warnings: CompletenessEntry[],
  mode: "dry-run" | "write",
  outDir?: string,
): string;
```

**CLI**:

```bash
tsx generator/run.ts --profile <path> [--validate-only | --dry-run | --out <dir>]
```

Los tres modos son mutuamente exclusivos (error → exit 2). Sin flags = `--validate-only` (compat con B3). `--out <dir>` requiere directorio vacío (exit 3 si no). `--dry-run` lista los 15 paths emitidos + tamaños sin tocar fs (6 docs + `policy.yaml` + 2 rules + 4 test harness + `ci.yml` + opcional `docs/BRANCH_PROTECTION.md`; el set exacto varía por stack y por `workflow.branch_protection`; ver § Renderers). Schema hard-coded a `questionnaire/schema.yaml`.

**Exit codes**:

- `0` — validación OK y, si aplica, render + escritura OK.
- `1` — `validateProfile` emitió issues **o** `completenessCheck` emitió errors. Render no se ejecuta.
- `2` — archivo ausente, YAML ilegible, args inválidos, modos mutuamente exclusivos combinados.
- `3` — `--out <dir>` target no vacío (protege output del usuario; `--force` fuera de scope).

**Composición**:

- [generator/lib/schema.ts](../generator/lib/schema.ts) — **re-export puro** de `parseSchemaFile` / `parseProfileFile` / `validateProfile` + tipos desde `tools/lib/`. 3ª aplicación de pattern-before-abstraction.
- [generator/lib/profile-loader.ts](../generator/lib/profile-loader.ts) — `loadProfile(path): Promise<LoadResult>` reusando `readAndParseYaml` de `tools/lib/read-yaml.ts`.
- [generator/lib/validators.ts](../generator/lib/validators.ts) — `completenessCheck(schema, profile): { errors, warnings }`. Exporta `USER_SPECIFIC_PATHS` para que los tests asseveren la lista sin duplicarla.
- [generator/lib/profile-model.ts](../generator/lib/profile-model.ts) — `buildProfile(file): Profile` expande dotted-answers a objeto nested (`setNested` que revienta ante colisiones de tipo), inyecta placeholders literales `TODO(identity.<campo>)` para los 3 user-specific paths faltantes, y emite `placeholders[]` para el reporter.
- [generator/lib/render-pipeline.ts](../generator/lib/render-pipeline.ts) — pipeline + I/O. Ver § Renderers.
- [generator/lib/handlebars-helpers.ts](../generator/lib/handlebars-helpers.ts) — helpers Handlebars (`eq`, `neq`, `includes`, `kebabCase`, `upperFirst`, `jsonStringify`) registrados sobre una instancia privada vía `Handlebars.create()`.
- [generator/lib/template-loader.ts](../generator/lib/template-loader.ts) — `loadTemplate(relativePath)` lee `templates/<path>` sincronamente al eval del módulo renderer y devuelve `CompiledTemplate`. 4ª aplicación de pattern-before-abstraction (evita duplicar el triple `create+registerHelpers+compile` en los 6 renderers).

**Deferrals de B3/C1** (documentados en [.claude/rules/generator.md](../.claude/rules/generator.md)):

- `generator/lib/token-budget.ts` — diferido hasta que `questionnaire/schema.yaml` declare `workflow.token_budget`.
- `--schema` flag — diferido hasta que exista 2º schema.
- `--force` flag — fuera de scope C1; `--out` sobre dir no vacío aborta con exit 3.

### Renderers (entregado en C1, ampliado en C2, C3, C4 y C5)

Un renderer por output. Función pura `Renderer = (profile: Profile) => FileWrite[]`. Sin efectos secundarios, sin `Date.now()`, sin `Math.random()`, sin env vars del host.

**`FileWrite` shape mínimo**:

```ts
type FileWrite = { path: string; content: string };
```

`path` es relativo al root del repo generado (permite subdirs: `.claude/rules/docs.md`). `mode` no existe en C1–C5 — se añadirá en la primera rama post-D1/E1a que copie ejecutables reales con bits de permiso. C5 sólo emite esqueleto `.claude/` (JSON + 2 READMEs), por lo que la extensión sigue sin justificarse.

**Pipeline** ([generator/lib/render-pipeline.ts](../generator/lib/render-pipeline.ts)):

```ts
export function renderAll(profile: Profile, renderers: Renderer[]): FileWrite[];
export async function writeFiles(outDir: string, files: FileWrite[]): Promise<void>;
export async function isDirEmpty(dir: string): Promise<boolean>;
```

`renderAll` concatena las salidas de los renderers y **falla explícitamente** ante colisión de paths (`throw` con índices de los dos renderers que colisionan). Es una invariante, no solo una aserción de tests. `writeFiles` crea subdirs con `mkdir -p`. `isDirEmpty` gate pre-escritura.

**Determinismo**: byte-identical entre runs. Tests asseveran con `JSON.stringify(renderAll(p, rs)) === JSON.stringify(renderAll(p, rs))`. Sin timestamps en templates (se añadirá `profile.metadata.generatedAt` inyectado desde fuera si una fase posterior lo requiere).

**Lista actual** (C1 + C2 + C3 + C4 + C5, 18 archivos por profile cuando `workflow.branch_protection == true`; 17 cuando `false`):

- **Core docs** (C1, tuple congelada `coreDocRenderers`): CLAUDE.md, MASTER_PLAN.md, ROADMAP.md, HANDOFF.md, AGENTS.md, README.md.
- **Policy + rules** (C2, tuple congelada `policyAndRulesRenderers`): `policy.yaml`, `.claude/rules/docs.md`, `.claude/rules/patterns.md`.
- **Tests harness** (C3, tuple congelada `testsHarnessRenderers`, 1 renderer): set variable por stack. `typescript+vitest` → `tests/README.md` + `tests/smoke.test.ts` + `vitest.config.ts` + `Makefile`. `python+pytest` → `tests/README.md` + `tests/test_smoke.py` + `pytest.ini` + `Makefile`.
- **CI/CD** (C4, tuple congelada `cicdRenderers`, 1 renderer): `.github/workflows/ci.yml` siempre (cuando `workflow.ci_host == "github"`); `docs/BRANCH_PROTECTION.md` sólo si `workflow.branch_protection == true`. `workflow.ci_host ∈ {gitlab, bitbucket}` → `Error` explícito desde el renderer ("deferred" + path del schema).
- **Skills + hooks skeleton** (C5, tuple congelada `skillsHooksRenderers`, 1 renderer): `.claude/settings.json` (`hooks: {}` + `_note` explicando la deferral; **sin** `permissions` baseline), `.claude/hooks/README.md` (documenta deferral a Fase D), `.claude/skills/README.md` (documenta deferral a Fase E). 3 FileWrite por profile, stack-agnostic. **No** copia hooks ejecutables ni skills reales; ambos diferidos a rama post-D1/E1a.

Composición expuesta como `allRenderers` en [generator/renderers/index.ts](../generator/renderers/index.ts) — `Object.freeze([...coreDocRenderers, ...policyAndRulesRenderers, ...testsHarnessRenderers, ...cicdRenderers, ...skillsHooksRenderers])`. `generator/run.ts` importa únicamente `allRenderers`; la composición no vive en `run.ts` para evitar que crezca por fase (decisión de Fase -1 de C2, consolidada como 5ª aplicación del patrón `renderer-group` en C5).

**`policy.yaml` — detalles del renderer**:

- Un solo template Handlebars ([templates/policy.yaml.hbs](../templates/policy.yaml.hbs)), no se fragmenta por secciones.
- `type: "generated-project"` hardcoded en el template.
- `project:` usa `{{answers.identity.name}}`, que `buildProfile` expande a `TODO(identity.name)` cuando el profile no resuelve el path (patrón user-specific heredado de C1).
- Conditionals stack inline (`{{#if (eq answers.stack.language "typescript")}}`) toggle `pre_push.checks_required` (npx tsc/vitest/eslint vs python3 mypy/pytest/ruff) y `testing.unit.framework_node` vs `framework_python`. Los tests validan que no se filtran claves del stack ajeno.

**`.claude/rules/` — detalles del renderer**:

- Un solo renderer (`rules.ts`) emite 2 archivos: `.claude/rules/docs.md` + `.claude/rules/patterns.md`. Otros rules (`generator.md`, `templates.md`, `tests.md`, `ci-cd.md`, `skills-map.md`) quedan fuera del scope C2 — se añadirán en ramas posteriores sólo si aparece señal de stack-specificidad real.
- `docs.md.hbs` cierra el carry-over Fase N+7 iniciado en C1 con el bullet "Trazabilidad de contexto" referenciando `HANDOFF.md §3`.
- `patterns.md.hbs` es doctrina stack-agnóstica (formato de un pattern file + hard rules + referencias a antipatterns/invariants).

**`tests/*` + harness configs — detalles del renderer** (C3):

- Un solo renderer (`tests.ts`) emite 4 archivos según la combinación `stack.language` + `testing.unit_framework`. Combinaciones soportadas en C3: `typescript+vitest` y `python+pytest` únicamente. Resto (`jest`, `go-test`, `cargo-test`) lanza `Error` explícito desde el renderer con el nombre del framework + la palabra "deferred" + referencia al path `testing.unit_framework` — NO se mueve a `run.ts` (decisión Fase -1 de C3: fallo testeable con contrato claro).
- `Makefile` es el entry-point universal (TS + Python). Targets: `test` (alias de `test-unit`), `test-unit`, `test-coverage`, `test-e2e` (placeholder sólo en TS, referencia al README), `clean`.
- `vitest.config.ts` / `pytest.ini` son configuraciones mínimas pero válidas. Coverage threshold parametrizado desde `answers.testing.coverage_threshold`.
- Smoke tests (`tests/smoke.test.ts` / `tests/test_smoke.py`) son funcionales reales (no placeholders): compilan/ejecutan y hacen una assertion trivial.
- **Qué NO emite C3** (documentado en el `tests/README.md` emitido): `package.json` (TS), `pyproject.toml` (Python), `playwright.config.ts` (sólo mención en el README cuando `testing.e2e_framework != "none"`). Scope C3 es "test harness estructuralmente coherente", no "proyecto ejecutable end-to-end". La instalación real del stack + config e2e completa quedan diferidas.
- `generator/__fixtures__/profiles/valid-partial/profile.yaml` declara `testing.coverage_threshold` + `testing.e2e_framework` explícitamente porque `buildProfile` no materializa defaults del schema todavía. Defaults-in-profile queda diferido a rama posterior.

**`.github/workflows/ci.yml` + `docs/BRANCH_PROTECTION.md` — detalles del renderer** (C4):

- Un solo renderer (`ci-cd.ts`) emite hasta 2 archivos según `workflow.ci_host` + `workflow.branch_protection`. Soportado en C4: `ci_host == "github"` únicamente. `gitlab` / `bitbucket` → `Error` explícito desde el renderer con host + "deferred" + path `workflow.ci_host` (mismo patrón que frameworks diferidos de C3; 0 repeticiones canónicas, CLAUDE.md regla #7).
- `ci.yml` es estable: `name: ci`, trigger `pull_request`/`push` a `main`, job único `unit` con `runs-on: ubuntu-latest`. Stack conditionals: `typescript` → step `setup-node` pinned + Node 20.17.0 + step `Install test deps` (`npm install --no-save vitest@3.0.5 @vitest/coverage-v8@3.0.5`, versiones pinneadas alineadas con `package.json` del meta-repo); `python` → step `setup-python` pinned + 3.11 + step `Install test deps` (`pip install pytest==8.3.4 pytest-cov==6.0.0`, también pinneadas). Cada `uses:` pinneado por SHA40 (regla `.claude/rules/ci-cd.md`). El workflow **invoca `make test-unit` y `make test-coverage`** exclusivamente — nunca `npx vitest` / `pytest` directos (entry-point universal delegado al `Makefile` emitido por C3). Los `${{ github.* }}` literales se escapan con `\{{` en el template para evitar interpretación de Handlebars.
- **Contrato del workflow** (cerrado en revisión de C4): el runner remoto NO depende de `package.json` / `pyproject.toml` emitidos (diferidos en C3). El step `Install test deps` instala las dependencias mínimas que el `Makefile` necesita en ambos stacks con versiones pinneadas (TS: `vitest` + `@vitest/coverage-v8`; Python: `pytest` + `pytest-cov`). Tests semánticos validan presencia + pins + orden pre-`make test-unit` en ambas ramas, más no-leak cruzado (TS sin `pip`/`pytest`; Python sin `npm`/`vitest`). Cuando C5/C6 emitan `package.json` / `pyproject.toml`, el step pasará a un `npm ci` / `pip install -e .[dev]` equivalente y los pins saldrán del manifest, no del workflow.
- `BRANCH_PROTECTION.md` es dinámico: lista los jobs reales del `ci.yml` emitido + los targets Makefile invocados. Tests de consistencia cruzada validan que ambos archivos se mantienen coherentes. Markdown para aplicación manual en GitHub Settings — el generador **no** llama la API de GitHub (separación control-plane vs runtime-plane, § 1).
- Runtime versions hardcoded en C4 (Node 20.17.0 coincide con `.nvmrc` del meta-repo; Python 3.11). Deuda documentada como futura rama en `.claude/rules/generator.md § Deferrals` (schema: añadir `stack.runtime_version`).
- `workflow.release_strategy` y `release.yml` diferidos: las 3 ramas de release strategy divergen en pasos distintos, requieren rama propia.
- `generator/__fixtures__/profiles/valid-partial/profile.yaml` declara `workflow.ci_host: "github"` + `workflow.branch_protection: true` explícitos (mismo workaround que C3 por defaults no materializados en `buildProfile`).

**`.claude/settings.json` + READMEs de `.claude/{hooks,skills}/` — detalles del renderer** (C5):

- Un solo renderer (`skills-hooks-skeleton.ts`) emite 3 archivos por profile, estrictamente estructurales, stack-agnósticos. Cierra la *estructura* del directorio `.claude/` del proyecto generado pero **no** copia hooks ejecutables ni skills reales.
- `.claude/settings.json` es JSON estático mínimo conservador: `{ "_note": "<deferral a Fase D>", "hooks": {} }`. **No** declara `permissions` baseline (decisión explícita del usuario en Fase -1: sembrar una superficie de permisos sin hooks reales sería arbitrario; Fase D decidirá cuando los hooks existan).
- `.claude/hooks/README.md` documenta que la copia real de hooks queda diferida a Fase D + la extensión prevista de `FileWrite` con `mode?: number` para preservar bit `+x`.
- `.claude/skills/README.md` documenta que la copia real de skills queda diferida a Fase E (catálogo auditado por `/pos:audit-plugin --self` antes de quedar activo).
- Tests validan: JSON parseable, `hooks === {}`, `_note` string >40 chars con `/pos/`, `permissions === undefined`, READMEs matching `/\bpos\b/` + `/Fase\s*D|E/` + `/diferid/i`, stack-agnostic (sin leaks `vitest`/`pytest`/`npm`/`pip`), trailing `\n`, determinismo byte-identical.
- 5ª aplicación del pattern `renderer-group` (tuple congelada `skillsHooksRenderers` compuesta en `allRenderers`). `run.ts` no se toca.

**Pendientes post-C***: copia real de hooks ejecutables + copia real de skills auditadas + extensión `FileWrite` con `mode?` para preservar bit `+x` — las tres diferidas a la misma rama post-D1/E1a (ver `.claude/rules/generator.md § Deferrals`).

**Cómo añadir un renderer**:

1. Crear `templates/<Nombre>.hbs` (Handlebars). Subdirs permitidos (p.ej. `templates/.claude/rules/docs.md.hbs` → emite a `.claude/rules/docs.md`).
2. Crear `generator/renderers/<x>.ts`:
   ```ts
   import { loadTemplate } from "../lib/template-loader.ts";
   import type { Renderer } from "../lib/render-pipeline.ts";
   const template = loadTemplate("<Nombre>.hbs");
   export const render: Renderer = (profile) => [
     { path: "<Nombre>", content: template(profile) },
   ];
   ```
3. Crear `generator/renderers/<x>.test.ts` primero (TDD): tests semánticos sobre paths emitidos + strings críticas + verificación de stack conditionals si aplica.
4. Registrar en el array correspondiente de [generator/renderers/index.ts](../generator/renderers/index.ts): `coreDocRenderers` (C1), `policyAndRulesRenderers` (C2), `testsHarnessRenderers` (C3), `cicdRenderers` (C4), o un **nuevo array congelado** si el renderer pertenece a un grupo nuevo. Componer el nuevo array dentro de `allRenderers`. `run.ts` no se toca.
5. Los snapshots por `profile × template` se autogeneran en `generator/__snapshots__/<slug>/*.snap` al correr vitest — revisar diff antes de commit. C1 aportó 18 (3 × 6); C2 los amplió a 27 (3 × 9); C3 los amplió a 39 (+12: 2 profiles TS × 4 templates + 1 profile Python × 4 templates); C4 los amplió a 45 (+6: 3 profiles × 2 archivos — `.github/workflows/ci.yml.snap` + `docs/BRANCH_PROTECTION.md.snap`). Los templates pueden variar por stack y por flags del profile, así que el conteo ya no es estrictamente `profiles × templates` desde C3.
6. Si el renderer requiere un nuevo helper Handlebars, añadirlo en [generator/lib/handlebars-helpers.ts](../generator/lib/handlebars-helpers.ts) con tests de compilación real.

**User-specific placeholders**: `buildProfile` inyecta literal `TODO(identity.name|description|owner)` cuando el profile no los declara. Los templates usan `{{answers.identity.name}}` directamente — no necesitan `{{#if}}` guards para estos tres. Emite warning por path vía `completenessCheck`; no bloquea emisión. La sustitución real pasará por el runner interactivo de fase posterior.

## 4. Hooks (Python)

### Por qué Python

- El ecosistema Claude Code documenta hooks en Python/bash.
- Stdlib suficiente (json, pathlib, subprocess, shlex, re).
- Type hints modernos (3.10+).
- Testeable con pytest sin friction.

### Inventario

| Hook | Evento | Entregado en |
|---|---|---|
| `pre-branch-gate.py` | PreToolUse(Bash) | D1 |
| `session-start.py` | SessionStart | D2 |
| `pre-write-guard.py` | PreToolUse(Write) | D3 |
| `pre-pr-gate.py` | PreToolUse(Bash) matcher gh/git | D4 |
| `post-action.py` | PostToolUse(Bash) | D5 |
| `pre-compact.py` | PreCompact | D6 |
| `stop-policy-check.py` | Stop | D6 |

Todos leen `policy.yaml` al inicio (cacheado por sesión vía hash del archivo).

### Protocolo

Input: JSON stdin con `tool_name`, `tool_input`, `session_id`, etc.
Output: JSON stdout con `hookSpecificOutput`, `permissionDecision`, `additionalContext`, `decisionReason`.
Exit: 0 = ok, 2 = blocking.

## 5. Skills (Claude Code Skills primitive)

Ver `.claude/rules/skills-map.md` para mapa completo. Primer conjunto real entregado en E1a (`project-kickoff` + `writing-handoff`).

### Primitive oficial (fijado en E1a)

Cada skill vive en `.claude/skills/<slug>/SKILL.md`. Frontmatter YAML **minimal**:

```yaml
---
name: <slug-kebab-case>               # coincide con el nombre del directorio. SIN prefijo `pos:` ni namespace.
description: Use when <disparadores>. # "Use when …" — selección eligible por el modelo, no trigger garantizado.
allowed-tools:                        # opcional. YAML list (no string).
  - Read
  - Bash(git log:*)
---

# <slug>

Cuerpo en markdown. Instrucciones declarativas al modelo + steps ejecutables.
```

**No inventar campos**. Fase -1 v1 de E1a propuso `context:` / `model:` / `agent:` / `effort:` / `hooks:` / `user-invocable:` por analogía con slash commands y con rules antiguas; fueron rechazados por no tener documentación oficial citable en el SDK. Si una versión futura del SDK los añade, se citan con fuente antes de introducirlos (rama propia). Si un consumo pesado requiere subagent, se delega via Agent tool desde el body de la SKILL.md (decisión abierta en E1b) en vez de extender frontmatter.

### Logging best-effort (helper compartido)

Toda skill cierra con una invocación Bash al helper compartido:

```bash
.claude/skills/_shared/log-invocation.sh <name> <status>
```

Shape de `.claude/logs/skills.jsonl` fijado en E1a (`{ts, skill, session_id, status}` — 4 campos, sin `args`, sin `duration_ms`). Fallback `session_id: "unknown"` si `CLAUDE_SESSION_ID` ausente. `mkdir -p` del log dir — crea si falta.

**Framing operacional, no criptográfico**: si el modelo omite el step (rare pero posible), el sistema pierde traza de esa invocación pero nunca rompe. `stop-policy-check.py` trata ausencia de entry como "no invocación" → allow (silencio ≠ violación). Extender el shape requiere rama propia + migración de `_extract_invoked_skills` + tests del contrato.

### Allowlist enforcement (D6 scaffold + E1a flip-switch)

`policy.yaml.skills_allowed` lista los skills que el repo acepta invocar. Contrato tri-estado de `skills_allowed_list(repo_root)` (D6 + post-review):

| Estado del campo                                   | Accessor devuelve             | `stop-policy-check.py` hace                    |
|----------------------------------------------------|-------------------------------|------------------------------------------------|
| Ausente                                            | `None`                        | `status: deferred` pass-through                |
| Presente pero mal formada (scalar / no-string…)    | `SKILLS_ALLOWED_INVALID`      | `status: policy_misconfigured` pass-through (observable) |
| `[]` (lista declarada vacía)                       | `()`                          | Enforcement live — deny-all                    |
| Lista poblada                                      | `tuple[str, ...]`             | Enforcement live — deny si invocación fuera    |

E1a flippa de "Ausente" a "Lista poblada" sin tocar código del hook — puro cambio declarativo en `policy.yaml`.

### Sustituciones soportadas

`$ARGUMENTS`, `$1..$N`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_SKILL_DIR}`, `` !`command` `` (shell injection, requiere `shell: true` en frontmatter).

## 6. Agents (plugin-owned subagents)

Top-level superficie del plugin: `agents/<slug>.md`. Cada archivo es un subagent definido en el primitive oficial de Claude Code (`name` + `description` + `tools` + `model`); el body Markdown actúa como system prompt. Los skills consumidoras los invocan vía `Agent(subagent_type="<slug>", ...)` con fallback a `general-purpose` si el runtime no los expone.

**Shape distinto al skill primitive** (Fase F2):

| Aspecto | Skill (`.claude/skills/<slug>/SKILL.md`) | Agent (`agents/<slug>.md`) |
|---|---|---|
| Tools | `allowed-tools:` YAML list | `tools:` comma-separated string |
| Modelo | No campo en frontmatter (corre en orchestrator) | `model:` requerido (sonnet por defecto en F2) |
| Body | Body es la skill instructions | Body es el system prompt del subagent |

**Namespace `pos-*` obligatorio** para evitar colisión con built-in defaults de Claude Code (`code-reviewer`, `code-architect`, `Plan`, `Explore`, `general-purpose`) y con user/project agents externos. Validado por `agents/tests/test_agent_frontmatter.py::TestFrontmatter::test_name_uses_pos_namespace`.

**Agents entregados (F2)**:

- `agents/pos-code-reviewer.md` — branch-diff review (bugs / logic / security / scope / invariants). Consumido por `pre-commit-review` (E2a). `tools: Read, Grep, Glob, Bash`. Hard limits: no `Edit`, no `Write`, no PR.
- `agents/pos-architect.md` — pattern extraction + cross-file design. Consumido por `compound` (E3a). `tools: Read, Grep, Glob, Bash`. Hard limits: no refactor, no overwriting de patterns existentes.

**Diferidos en F2 (regla #7 CLAUDE.md — ≥2 repeticiones antes de abstraer)**:

- `pos-auditor` — sin consumer real hoy. Reabrir cuando una skill futura lo requiera.
- `policy.yaml.agents_allowed` — sin enforcement consumer (Stop hook lee `skills.jsonl`, no hay log de invocaciones de subagents). Reabrir cuando un hook futuro requiera enforcement.

**Forward-compat negation**: skills main-strict (`pattern-audit` E3a, `audit-session` F1) **nunca** referencian plugin subagents — los tests `test_skill_frontmatter.py` lockean esto vía negation lists.

## 7. Determinismo — tres capas

### Capa 1: Hooks (unchallengeable)

Código Python/bash. Exit code 2 = bloqueo. El LLM no puede ignorarlos. Son el último recurso de enforcement.

**Tres variantes canónicas** según el evento:

- **Blocker** (PreToolUse / PreCompact / Stop): safe-fail estricto — payload malformado → `deny` + exit 2 + `decisionReason`. El hook no puede dejar pasar lo que no puede validar. Referencia: `hooks/pre-branch-gate.py` (D1).
- **Informative** (SessionStart): safe-fail graceful — nunca emite `permissionDecision`, nunca exit 2. Payload malformado → `additionalContext` mínimo + entrada en `session-start.jsonl` vía `_log_error` (no se escribe a `phase-gates.jsonl`). Errores de git/subprocess → `additionalContext` mínimo + `_log_snapshot` sigue emitiendo la entrada happy-path (`branch=None`, `phase="unknown"`) en ambos logs; lo que se omite es la entrada de *error* (absorbidos por `_git` como `None`, sin `_log_error`). Fallos del propio logging (disk full, read-only fs) se tragan vía `_safe_append`. Exit 0 siempre. Bloquear un evento informativo dejaría al usuario sin contexto sin ganancia de enforcement. Referencia: `hooks/session-start.py` (D2).
- **PostToolUse non-blocking** (PostToolUse): safe-fail no-op — payload malformado / `tool_name != "Bash"` / command ausente o vacío / comando que no matchea el classifier → early return 0 silencioso (sin stdout, sin log). En happy path puede emitir `hookSpecificOutput.additionalContext` sugiriendo acciones al usuario. Nunca emite `permissionDecision`, nunca exit 2. Bloquear un PostToolUse es inviable — la acción ya ocurrió; el patrón útil es degradar a advisory. Referencia: `hooks/post-action.py` (D5).

**Implementación canónica blocker — `hooks/pre-branch-gate.py`** (entregado en rama D1):

- Shebang `#!/usr/bin/env python3` + stdlib-only (json, shlex, sys, pathlib).
- Lee JSON de stdin; `permissionDecision: deny` + `decisionReason` en stdout cuando bloquea.
- Exit codes: `0` en allow + pass-through; `2` en bloqueo y en payload malformado (stdin vacío, JSON inválido, top-level no-dict, `tool_input` no-dict para un `Bash` call).
- Pass-through silencioso (sin stdout, sin log) para non-Bash tools, `tool_input` ausente o `null`, `command` vacío, y comandos Bash que no crean rama.
- Detección con `shlex.split` (robusto a quoting + global options git pre-subcommand).
- Double log: `.claude/logs/<hook-name>.jsonl` propio + `.claude/logs/phase-gates.jsonl` (evento canónico del ciclo, p.ej. `branch_creation`).

**Implementación canónica informative — `hooks/session-start.py`** (entregado en rama D2):

- Shebang + stdlib-only (json, re, subprocess, sys, pathlib).
- Emite `hookSpecificOutput.additionalContext` con snapshot ≤10 líneas (Branch / Phase / Last merge / Warnings).
- Fase derivada vía regex `^(feat|fix|chore|refactor)[/_]([a-z])(\d+)-` sobre nombre de rama; en `main`/`master` fallback a `.claude/logs/phase-gates.jsonl` (último evento con slug parseable). `unknown` si ninguna fuente resuelve.
- Warnings: marker ausente (`.claude/branch-approvals/<sanitized>.approved`) + docs-sync pendiente (diff `main..HEAD` sin tocar `ROADMAP.md` ni `HANDOFF.md`). Suprimidos en `main`/`master` y cuando git no está disponible.
- Subprocess git con `shell=False`, `cwd=` explícito, `timeout=2`, `check=False`, captura `FileNotFoundError` + `SubprocessError`; `None` en cualquier error — el caller decide degradación.
- Exit 0 siempre. Payload malformado → snapshot mínimo `(error reading payload: ...)` + log a `.claude/logs/session-start.jsonl`. `phase-gates.jsonl` sólo recibe el evento `session_start` en el happy path (parse OK). Nunca emite `permissionDecision`.

**Segunda aplicación blocker — `hooks/pre-write-guard.py`** (entregado en rama D3):

- Shape idéntico a D1. Regla específica: enforza CLAUDE.md regla #3 sobre `hooks/*.py` top-level + `generator/**/*.ts`.
- Clasificador con dos buckets de exclusión separados (tests/docs/templates/meta vs helper internals `hooks/_lib/**`); contrato y tablas en [.claude/rules/hooks.md § Tercer hook](../.claude/rules/hooks.md).
- Double log propio + `phase-gates.jsonl` (evento `pre_write`). Pass-throughs no loguean (replica D1); allow sobre impl existente sí loguea (trazabilidad edit flow).
- Scope recortado en Fase -1 (pattern injection + anti-pattern blocking diferidos post-E3a): ver [MASTER_PLAN.md § Rama D3](../MASTER_PLAN.md).

**Tercera aplicación blocker — `hooks/pre-pr-gate.py`** (entregado en rama D4):

- Shape idéntico a D1. Regla específica: enforza CLAUDE.md regla #2 (docs-sync dentro de la rama) sobre `gh pr create`.
- Matcher via `shlex.split`: sólo activa si `tokens[:3] == ["gh", "pr", "create"]`; cualquier otro comando Bash → pass-through silencioso.
- Docs-sync = required `ROADMAP.md` + `HANDOFF.md` (obligatorio en todo PR) + condicionales por prefijo de path tocado calculado vía `git merge-base HEAD main` + `git diff --name-only <base> HEAD`: `generator/` y `.claude/patterns/` → `docs/ARCHITECTURE.md`; `hooks/` (excluyendo `hooks/tests/`) → `docs/ARCHITECTURE.md`; `skills/` → `.claude/rules/skills-map.md`. Reglas hardcoded — mirror literal de `policy.yaml.lifecycle.pre_pr.docs_sync_required`/`docs_sync_conditional` (parse deferido a rama policy-loader, CLAUDE.md regla #7).
- **Divergencia deliberada `hooks/tests/` vs policy**: el hook excluye `hooks/tests/` del trigger condicional; `policy.yaml` lista `hooks/**` uniforme. Motivo semántico — editar tests no altera arquitectura y no debe forzar docs-sync arquitectural. Reconciliación (policy granular o loader con excepción) diferida a la rama policy-loader; el loader decidirá la forma canónica.
- `decisionReason` lista los docs ausentes más los paths que los dispararon (capados a 3 por doc + sufijo `... (+N more)` cuando desbordan). Distinción empty-diff vs diff-no-disponible: `diff_files` devuelve `list[str] | None`; `None` (git subprocess falló tras merge-base OK) → skip advisory con `status: "skipped", reason: "git diff unavailable"`; `[]` (diff verdaderamente vacío, branch sin commits) → deny con razón dedicada (`empty PR`). Evita false-deny cuando git falla.
- Advisory scaffold (`skills_required`, `ci_dry_run_required`, `invariants_check`) persistido como entradas `status: deferred` en el log del hook sólo cuando se emite decisión real (allow/deny con diff). Las skills y los invariants llegan en fases E*/F; el shape queda preparado sin bloquear.
- Skip advisory (pass-through sin decisión + log `skipped`) en: `main`/`master`, `HEAD` detached, git no disponible, `merge-base HEAD main` sin resolver, `git diff` no disponible. Bloquear esos caminos dejaría al usuario sin vía para crear PRs antes de que haya historia contra `main`, o lo bloquearía por fallos transitorios de git.
- Safe-fail blocker canonical (D1): stdin no-JSON / top-level no-dict / `tool_input` no-dict → deny exit 2. `command` ausente, no-string o vacío → pass-through exit 0 (payload válido pero fuera de scope).
- Double log: `.claude/logs/pre-pr-gate.jsonl` (`{ts, hook, command, decision, reason}`) + `.claude/logs/phase-gates.jsonl` (evento `pre_pr`, `{ts, event, decision}`). Pass-throughs no loguean (replica D1); los skips advisory sí loguean con `status: skipped` para dejar rastro.
- Reuso `_lib/`: `append_jsonl` + `now_iso`. `sanitize_slug` no aplica (D4 no deriva slugs). No introduce helpers nuevos a `_lib/` (regla #7: sólo cuando ≥2 hooks lo reclamen).

**Implementación canónica PostToolUse non-blocking — `hooks/post-action.py`** (entregado en rama D5):

- Shebang + stdlib-only (fnmatch, json, shlex, subprocess, sys, pathlib).
- Detección jerárquica 2 tiers que separa intención (comando) de resultado (reflog):
  - **Tier 1** (`shlex.split(command)`, `tokens[0] == "git"`): matcher A `tokens[1] == "merge"` y ningún token en `{--abort, --quit, --continue, --skip}`; matcher C `tokens[1] == "pull"` y ningún token en `{--rebase, -r}`. Otros comandos (`git rebase`, `git status`, `gh pr merge`, non-git) → early return 0 silencioso.
  - **Tier 2** (post-hoc, `git reflog HEAD -1 --format=%gs`): matcher A confirma si el mensaje comienza por `"merge "`; matcher C confirma si comienza por `"pull:" | "pull "` y NO por `"pull --rebase"`. Descarta falsos positivos (p.ej. `git merge --ff-only` que no pudo fast-forward y no tocó HEAD; `git pull` que terminó siendo rebase sin flag explícito).
- Cuando ambos tiers confirman: deriva paths tocados via `git diff --name-only HEAD@{1} HEAD`; matchea con `fnmatch.fnmatch` contra `TRIGGER_GLOBS` literal mirror de `policy.yaml.lifecycle.post_merge.skills_conditional[0].touched_paths_any_of` (`generator/lib/**`, `generator/renderers/**`, `hooks/**`, `skills/**`, `templates/**/*.hbs`), respetando `SKIP_IF_ONLY_GLOBS` (`docs/**`, `*.md`, `.claude/patterns/**`) y `MIN_FILES_CHANGED = 2`. Match → emite `hookSpecificOutput.additionalContext` con 4 líneas: encabezado, lista de globs matched, `Touched: <cap 3 + "(+N more)">`, CTA `Consider running /pos:compound...`.
- **Advisory-only**. El hook nunca dispatcha `/pos:compound` — mantiene separación control-plane (hooks enforcement) vs skill-plane (comportamiento dirigido por LLM). La skill real la entrega E3a; dispatch desde hook sería antipatrón canonizado.
- Exit 0 siempre. Payload malformado, `tool_name != "Bash"`, `command` ausente/vacío, shlex unparsable, Tier 1 miss → early return 0 **sin log** (pass-through silencioso, replica D1). Los paths advisory (Tier 2 no confirma / diff no disponible) sí loguean al hook log pero NO a `phase-gates.jsonl` — la puerta del lifecycle `post_merge` sólo se cruza cuando hay merge/pull confirmado tocando paths observables.
- Subprocess git robusto (reusa patrón D2): `shell=False`, `cwd=Path.cwd()`, `timeout=5`, `check=False`, captura `FileNotFoundError` + `SubprocessError`; `None` en cualquier error — el caller degrada a advisory.
- Double log: `.claude/logs/post-action.jsonl` con 4 status distinguidos (`tier2_unconfirmed`, `diff_unavailable`, `confirmed_no_triggers`, `confirmed_triggers_matched`) + `.claude/logs/phase-gates.jsonl` con evento `post_merge` sólo en los dos status confirmed.
- Reuso `_lib/`: `append_jsonl` + `now_iso`. Sin nuevos helpers compartidos.
- **Segunda repetición hardcoded de `policy.yaml` tras D4**. Regla #7 CLAUDE.md cumplida dos veces (D4 = docs-sync required/conditional; D5 = post_merge skills_conditional) → precondición abierta para la rama policy-loader (post-D6) que unifique ambos parseos declarativamente.

**Segunda aplicación informative — `hooks/pre-compact.py`** (entregado en rama D6):

- Shape idéntico a D2. Shebang + stdlib + `_lib/` (`policy.pre_compact_rules`, `append_jsonl`, `now_iso`).
- Evento PreCompact. Lee `lifecycle.pre_compact.persist` vía `pre_compact_rules(cwd)` y emite `hookSpecificOutput.additionalContext` con checklist de items a persistir antes de la truncación. Exit 0 siempre; nunca `permissionDecision`. Bloquear `/compact` invocado por el usuario sería destructivo — el patrón útil es prompt-engineering al modelo, no enforcement.
- Trigger `auto`/`manual` (payload field) registrado en el log pero sin efecto sobre la salida; la checklist es la misma en ambos caminos.
- Failure mode (c.2) canonical: policy missing / malformed / sin sección `pre_compact` → log `status: policy_unavailable` + `additionalContext` mínimo advisory señalando que la policy no está disponible. Nunca deny blind — misma política canonizada por D5b para los tres hooks consumidores del loader. Wording exacto del advisory **no es contrato** (la suite valida shape + presencia, no string literal).
- Safe-fail informative (excepción D2 reforzada): stdin vacío / JSON inválido / top-level no-dict / lista / escalar → exit 0 + `additionalContext` mínimo describiendo el error de payload + log `status: payload_error`. Nunca `permissionDecision`, nunca exit 2. Wording exacto **no es contrato** (idem).
- Double log: `pre-compact.jsonl` siempre; `phase-gates.jsonl` evento `pre_compact` **sólo en happy path** (los caminos `policy_unavailable` y `payload_error` quedan aislados en el hook log — la puerta del lifecycle no se cruza sin checklist real emitido).

**Cuarta aplicación blocker (scaffold) — `hooks/stop-policy-check.py`** (entregado en rama D6):

- Shape idéntico a D1/D3/D4 (safe-fail blocker canónico). Evento Stop. Objetivo: validar que las skills invocadas en una sesión están en `policy.yaml.skills_allowed`.
- **Scaffold activable, NO enforcement en producción hoy** — `policy.yaml.skills_allowed` no existe todavía en el meta-repo; el accessor `skills_allowed_list()` devuelve `None` y el hook degrada a `status: deferred` pass-through. La cadena de enforcement (extractor → validator → deny) vive en código y está ejercida end-to-end por fixtures, pero en prod hoy es un no-op controlado. Cuando E1a (o posterior) añada el campo, el hook enforza sin refactor.
- Fuente de invocaciones: `.claude/logs/skills.jsonl` (canonical audit log declarado en `policy.yaml.audit.required_logs`). Helper `_extract_invoked_skills(repo_root, session_id) → list[str]` stream-parsea línea a línea (memoria acotada), filtra por `session_id` del payload Stop, e ignora líneas corruptas, entries non-dict, sin `skill`, `skill` no-string, o con `session_id` ausente / no-string / de otra sesión. Helper `_validate(invoked, allowed) → (decision, violations)` valida set-inclusion; deny si cualquier violation.
- Contrato **tri-estado** del accessor `skills_allowed_list` (post-review): **`None` = campo absent (deferred)** vs **`SKILLS_ALLOWED_INVALID` sentinel = presente pero mal formado (misconfigured observable)** vs **`()` = lista declarada-vacía (deny-all explícito)** vs **tupla poblada = enforcement live**. La distinción invalid/absent es obligatoria — colapsarlas haría que un typo en la policy apague enforcement silenciosamente como si fuera deferred legítimo.
- Cuatro caminos de decisión real:
  1. `policy.yaml` missing/malformed → log `status: policy_unavailable`, pass-through exit 0 (cero stdout). Mismo shape que los otros hooks tras D5b.
  2. `policy.yaml` OK sin `skills_allowed` → log `status: deferred`, pass-through exit 0. **Estado actual de prod**.
  3. `skills_allowed` presente pero mal formada → loader devuelve `SKILLS_ALLOWED_INVALID`; log `status: policy_misconfigured`, pass-through exit 0. **Distinto de deferred** — observable en el hook log.
  4. `skills_allowed` declarado como lista válida (incl. `[]`) → `_extract_invoked_skills(root, session_id)` + `_validate(invoked, allowed)`. Violación → deny exit 2 con primer violador + guía literal `"Add it to the allowlist or revert the invocation."` en `decisionReason`. Sin violaciones → allow exit 0.
- **Session scoping** (post-review): el extractor filtra `skills.jsonl` por `session_id` del payload Stop. El log es append-only y se contamina entre sesiones — sin scope, una skill rogue de ayer bloquearía el Stop de hoy. Payload Stop sin `session_id` (o no-string, o vacío) → safe-fail deny (no se puede scopiar enforcement).
- Safe-fail blocker canonical (D1/D3/D4): stdin vacío / JSON inválido / top-level no-dict / `session_id` ausente o no-string → deny exit 2 con `permissionDecision: deny` + `decisionReason` explicando la malformación. Un hook que no puede validar ni scopiar su input no debe dejarlo pasar (contrato reforzado desde D1).
- Double log **sólo en decisiones reales**: `stop-policy-check.jsonl` (`{ts, hook, session_id, decision, ...}` — con `violations` list en deny, `invoked_count` en allow) + `phase-gates.jsonl` evento `stop` (con `session_id` + `decision`). Los status advisory (`deferred`, `policy_misconfigured`, `policy_unavailable`) quedan sólo en el hook log — la puerta del lifecycle no se cruza hasta que la enforcement está realmente activa.
- Reuso `_lib/`: `policy.load_policy` + `policy.skills_allowed_list` + `policy.SKILLS_ALLOWED_INVALID` + `append_jsonl` + `now_iso`. Sin nuevos helpers compartidos — los privados `_extract_invoked_skills` y `_validate` son específicos del dominio Stop (no se repiten en otros hooks) y viven dentro del propio archivo.

**Helpers compartidos — `hooks/_lib/`** (extraído en D2 tras segunda repetición, CLAUDE.md regla #7):

- `_lib/slug.py::sanitize_slug` (`/` → `_`).
- `_lib/jsonl.py::append_jsonl` (append-only JSONL).
- `_lib/time.py::now_iso` (UTC ISO-8601).
- `_lib/policy.py` (D5b) — loader declarativo de `policy.yaml`. Ver bloque siguiente.
- Consumidos desde hooks con nombre hyphenated via `sys.path.insert(0, str(Path(__file__).parent))` + `from _lib.X import Y  # noqa: E402` (sin convertir el hook a package formal). Las ramas D3..D6 deben reusar estos helpers en lugar de redefinir; añadir a `_lib/` sólo cuando ≥2 hooks usen el nuevo helper.

**Loader declarativo `hooks/_lib/policy.py`** (entregado en rama D5b, refactor que cierra la precondición regla #7 abierta por D4 + D5):

- Fuente única de verdad para los hooks D3/D4/D5 frente a `policy.yaml`. Los tres hooks pasaron de mirror literal hardcoded a consumo declarativo en el mismo PR. Ningún nuevo hook (D6 en adelante) debe re-hardcodear — el patrón canónico es añadir un accessor tipado nuevo si la sección que consume no está cubierta todavía.
- API: `load_policy(repo_root)` con cache keyed por path abs únicamente — **sin componente mtime/size, sin invalidación implícita por edits al archivo**; `reset_cache()` para tests o para forzar recarga explícita) + 5 dataclasses congeladas (`ConditionalRule`, `DocsSyncRules`, `PostMergeTrigger`, `EnforcedPattern`, `PreWriteRules`) + 3 accessors tipados (`docs_sync_rules(repo_root)` / `post_merge_trigger(repo_root)` / `pre_write_rules(repo_root)`) + `derive_test_pair(rel_path, label)` con dos ramas label-driven (`hooks_top_level_py`, `generator_ts`).
- **Split declarativo vs procedural** (decisión b.1 Fase -1): strings y globs viven en YAML; derivación de paths (e.g. `hooks/foo.py` → `hooks/tests/test_foo.py`) vive en Python keyed por `label`. Descartado un YAML DSL — una sola derivación real no justifica el aparato; endurecería el contrato prematuramente.
- **Failure mode canónico (decisión c.2 Fase -1)**: `policy.yaml` ausente o corrupto → accessor devuelve `None` → hook consumidor degrada a **pass-through advisory** con entrada `status: policy_unavailable` en su propio log, sin cruzar `phase-gates.jsonl`. Nunca deny blind (evita brickear PRs ante un typo YAML) ni fallback hardcoded (rompería el propósito del loader). Esta política se canoniza como tercera variante de safe-fail en la Capa 1 (junto con blocker estricto e informative graceful).
- Dependencia: `pyyaml==6.0.2` (pin exacto, primera línea no-stdlib en `hooks/_lib/`). Justificado en kickoff D5b: no hay parser YAML en stdlib; escribir uno a mano sobre nuestro schema sería código muerto. Pin exacto (no range) porque la superficie es pequeña y los hooks son eventualmente consistencia crítica — upgrade explícito preferible.
- Fuente de la convergencia hook↔policy `hooks/tests/**`: al migrar D4 al loader, la excepción (que antes era una divergencia deliberada documentada en D4) se movió a `policy.yaml.lifecycle.pre_pr.docs_sync_conditional.hooks/**.excludes: ["hooks/tests/**"]`. Policy + hook ya son fuente única coherente.
- Pattern match nota técnica: `fnmatch.fnmatchcase` no es recursivo en el middle `/` (`generator/**/*.ts` NO matchea `generator/run.ts`). El bloque `pre_write.enforced_patterns` usa DOS entries con la misma `label: "generator_ts"` — una con `match_glob: "generator/*.ts"` y otra con `match_glob: "generator/**/*.ts"` — para cubrir top-level + subdirs.

**Drift temporal meta-repo ↔ template (abierto tras D5b)**: `templates/policy.yaml.hbs` + `generator/renderers/policy.ts` + los snapshots `generator/__snapshots__/<profile>/policy.yaml.snap` **NO fueron tocados** en la rama D5b. Consecuencia: un proyecto generado hoy con `pos` emite un `policy.yaml` **desactualizado** respecto al que vive en este meta-repo (sin `pre_write.enforced_patterns`, sin `excludes` en `hooks/**`). No es un bug del generador — es un drift intencional para no saturar la rama de refactor. La rama reconciliadora (update template + renderer + snapshots + añadir `pyyaml` al requirements-dev emitido para stacks Python) queda diferida a post-D6. **Este bloque NO debe leerse como "el template ya refleja el nuevo shape"** — explícitamente no lo refleja. Ver [MASTER_PLAN.md § Rama D5b](../MASTER_PLAN.md), [ROADMAP.md § refactor/d5-policy-loader](../ROADMAP.md), [HANDOFF.md §11](../HANDOFF.md).

### Capa 2: Logs auditables

`.claude/logs/`:
- `skills.jsonl` — cada invocación de skill (nombre, args, timestamp, duración, session_id, exit).
- `hooks.jsonl` — cada ejecución de hook (evento, decision, reason).
- `phase-gates.jsonl` — pasos de lifecycle alcanzados (branch_creation, pre_commit, pre_pr, post_merge).
- `drift.jsonl` — antipatterns detectados.
- `tests.jsonl` — runs de tests locales (archivo, resultado, duración).

Append-only. Hooks posteriores leen los logs para decidir bloqueo.

### Capa 3: Skill `/pos:audit-session`

Corre semanal (o on-demand). Compara `policy.yaml` declarativo vs logs reales:

- ¿Cada rama creada tuvo marker + branch-plan log?
- ¿Cada PR pasó por simplify + pre-commit-review?
- ¿Cada merge con touched_paths matching disparó compound?
- ¿Algún hook tuvo >3 timeouts (señal de script roto)?

Output: report en `.claude/logs/audit-YYYY-WW.md`. Muestra skips + sugiere fixes.

## 8. Token efficiency — aplicación

Ver `docs/TOKEN_BUDGET.md` para las reglas. Resumen:

- CLAUDE.md ≤200 líneas. Rules path-scoped ≤30KB total.
- SessionStart hook emite snapshot minimal (no carga HANDOFF entero).
- Skills pesadas con `context: fork`.
- Model routing: sonnet default, opus sólo architecture/critical, haiku lookups.
- Auto-compact managed (`compact_20260112`) configurado para scripts `claude -p` generados.
- Tool-result clearing (`clear_tool_uses_20250919`) para sesiones largas.

## 9. Pattern registry & compound

Ver `.claude/rules/patterns.md` para formato.

### Trigger de `/pos:compound` (post-merge)

Declarativo en `policy.yaml.lifecycle.post_merge.skills_conditional`. Ejemplo:

```yaml
- skill: "pos:compound"
  trigger:
    touched_paths_any_of:
      - "generator/lib/**"
      - "hooks/**"
      - "skills/**"
    skip_if_only:
      - "docs/**"
      - "*.md"
    min_files_changed: 2
```

No dispara si:
- Sólo se tocaron docs.
- Sólo se tocó `.claude/patterns/**` (evita recursión infinita con sus propios outputs).
- Menos de `min_files_changed`.

### Output

PR separado `chore/compound-YYYY-MM-DD` con:
- Archivos nuevos en `.claude/patterns/<area>/<nombre>.md`.
- Evidencia: enlaces a commits + diffs minimales.
- `evidence` requiere ≥2 commits distintos (enforce por hook).

## 10. Testing — tres niveles

### Local (pre-push)

- Unit (vitest/pytest).
- Integration.
- Selftest (`bin/pos-selftest.sh`): escenarios end-to-end con proyecto sintético (ver subsección).
- Coverage gate (threshold de `policy.yaml.testing.unit.coverage_threshold`).

Hook `pre-push.sh` corre todos antes de permitir `git push`.

### CI (GitHub Actions)

Mismo set que local + matriz (2 OS × 2 versiones runtime). Branch protection requiere todos verdes para merge a main.

### Selftest end-to-end (entregado en F3)

`bin/pos-selftest.sh` cierra el círculo "lo que el plugin promete enforce-ar contra repos generados, lo prueba sobre uno generado al vuelo". Estructura:

- **Wrapper** `bin/pos-selftest.sh` (bash mínimo): `#!/usr/bin/env bash` + `set -euo pipefail` + delega a `python3 bin/_selftest.py`. Sin lógica; entrypoint estable que tests + CI consumen sin path absoluto.
- **Orquestador** `bin/_selftest.py` (stdlib only, sin deps externas). Por escenario:
  1. crea tmpdir,
  2. ejecuta `npx tsx generator/run.ts --profile questionnaire/profiles/cli-tool.yaml --out <tmpdir>` (la generator real, no fixture committeado),
  3. sobre-escribe la sección mínima de `synthetic/policy.yaml` sólo cuando el escenario necesita un setup distinto del baseline emitido por el template (D3 inyecta un `enforced_patterns` no vacío sobre la lista vacía del template; D6 inyecta una `skills_allowed` sobre la clave omitida; D4 y D5 corren contra el baseline tras el cierre de drift en `refactor/template-policy-d5b-migration`),
  4. monta el sintético como git repo (`git init -b main` + commit baseline),
  5. invoca el hook real (`hooks/<name>.py`) vía subprocess con payload JSON,
  6. asserta exit code + presencia de tokens en stdout/stderr/files,
  7. imprime `[ok] D{N} {name}` o `[fail] D{N} {name}: <diag>`.
- **Pytest harness** `bin/tests/test_selftest_smoke.py` (4 tests, contrato del wrapper) + `bin/tests/test_selftest_scenarios.py` (5 tests, fixture module-scoped que corre `pos-selftest.sh` una vez y comparte stdout).

**Escenarios cubiertos** (5 funcionales-críticos): D1 pre-branch-gate, D3 pre-write-guard, D4 pre-pr-gate, D5 post-action (advisory `/pos:compound`), D6 stop-policy-check. **Out of scope**: D2 session-start + D6 pre-compact (informative, sin contrato deny/allow), Claude Code runtime (no instancia Claude, no invoca skills/agents reales — cobertura estática queda en `agents/tests/test_agent_frontmatter.py` y `.claude/skills/tests/test_skill_frontmatter.py`), D5b loader (cubierto indirectamente vía hooks consumidores).

**CI**: nuevo job `selftest` en `.github/workflows/ci.yml` (ubuntu × Python 3.11, single matrix — gates funcionales platform-agnostic; matriz extendida sería sobre-promesa). Comando único: `pytest bin/tests -q`. Ejecución end-to-end local ~1.2s.

**Drift cerrado** (`refactor/template-policy-d5b-migration`, post-F4): `templates/policy.yaml.hbs` migrado al shape contractual con el loader (`pre_write.enforced_patterns: []`, `pre_pr.docs_sync_conditional: []`, `pre_compact.persist` con los 3 items canónicos, `post_merge.skills_conditional[0].trigger` con globs genéricos conservadores, `skills_allowed` omitido por diseño). Contrato lockdown vía `bin/tests/test_template_loader_contract.py` corriendo los accessors reales del loader contra el output del generador real sobre los 3 profiles canónicos. `bin/_selftest.py` removió los overlays de D4 y D5; D3 y D6 mantienen overlays mínimos por diseño (A1 emite lista vacía, A2 omite la clave).

### Generador emite test harness

El generador emite, según stack del profile:
- Config de framework (vitest.config.ts, pytest.ini, etc.).
- Scripts en package.json / Makefile.
- Ejemplo de smoke test en `tests/smoke/`.
- `tests/README.md` con guía rápida.
- `.github/workflows/ci.yml` alineado con checks locales.

## 11. CI/CD integrado

Ver `.claude/rules/ci-cd.md`. Principios:

- Nada en CI que no corra local primero.
- Workflows pinneados por SHA.
- Secrets vía `secrets.*`, nunca hardcoded.
- Coverage gate en CI usando threshold de `policy.yaml` (delegado al `Makefile` vía `make test-coverage`).
- Branch protection documentada en `docs/BRANCH_PROTECTION.md` (aplicación manual en GitHub Settings).

### Qué emite C4

El renderer `ci-cd.ts` (tuple `cicdRenderers`) emite hasta 2 archivos por profile, gobernados por `workflow.ci_host` + `workflow.branch_protection`:

- **`.github/workflows/ci.yml`** — siempre que `ci_host == "github"`. Workflow mínimo estable (`name: ci`, job `unit` sobre `ubuntu-latest`). Stack conditionals para setup runtime (Node 20.17.0 / Python 3.11). `uses:` pinneados por SHA40. El workflow invoca `make test-unit` + `make test-coverage` exclusivamente — el Makefile emitido por C3 es el entry-point universal.
- **`docs/BRANCH_PROTECTION.md`** — sólo si `branch_protection == true`. Markdown dinámico que lista los jobs reales del `ci.yml` emitido. Aplicación manual en GitHub Settings (el generador no llama la API de GitHub: separación control-plane vs runtime-plane, § 1).

### Qué queda diferido (C4)

- **`ci_host ∈ {gitlab, bitbucket}`**: `Error` explícito desde el renderer con host + "deferred" + path `workflow.ci_host`. 0 repeticiones en profiles canónicos (CLAUDE.md regla #7); reabrir cuando un profile canónico los adopte.
- **`release.yml`**: las 3 ramas de `workflow.release_strategy` divergen en pasos distintos (publish vs tag-only vs push-on-main), mezclar en C4 duplica complejidad. Rama propia futura.
- **`audit.yml` / nightly workflows**: dependen de infra (secrets, cron triggers) que excede el scope del harness mínimo.
- **Matriz multi-OS / multi-runtime**: C4 emite `ubuntu-latest` + runtime único (20.17.0 / 3.11). Matrix real se difiere hasta que `stack.runtime_version` exista en el schema.
- **Runtime versions en schema**: hardcoded en C4. Rama futura = añadir `stack.runtime_version` a `questionnaire/schema.yaml` + cablear en el template.

## 12. Safety para community tools

Ver `docs/SAFETY_POLICY.md`. Resumen:

- Fuentes confiables rankeadas: Anthropic MCP registry > plugins `@anthropics/*` > autores verificados con historial.
- Checklist obligatorio antes de instalar: manifest, hooks, MCP args, permisos, pin de versión.
- Denylist con razón documentada.
- Starter opt-in: sólo MemPalace y PleasePrompto/notebooklm-mcp (Fase B).

## 13. Marketplace público + release flow (entregado en F4)

Plugin `pos` se publica vía:

1. **Manifest local** [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) — schema oficial Claude Code marketplace. Top-level `{name, owner, plugins[]}`. Cada plugin: `{name, source: {source, repo, ref}, version, description}`. Source of truth de qué publica este repo.
2. **Versión canonical** [`.claude-plugin/plugin.json`](../.claude-plugin/plugin.json) `version`. Tag git = `v${version}`. `marketplace.json.plugins[0].source.ref` mirror-ea el tag.
3. **Workflow** [`.github/workflows/release.yml`](../.github/workflows/release.yml) — trigger `push.tags: ['v*']`. Cinco jobs encadenados:
   - `version-match` (gate inicial: `plugin.json.version == ${tag#v}`).
   - `selftest` (reusa contrato F3).
   - `build-bundle` (curated plugin-only `tar.gz`).
   - `publish-release` (`needs: [version-match, selftest, build-bundle]`; `gh release create` con bundle).
   - `mirror-marketplace` (condicional `if: vars.POS_MARKETPLACE_REPO != ''`; abre PR en repo público; skippea silenciosamente si no configurado).
4. **Bundle scope** — plugin-only curated: `.claude-plugin/`, `.claude/skills/`, `.claude/rules/`, `hooks/`, `agents/`, `policy.yaml`, `bin/pos-selftest.sh`, `bin/_selftest.py`, `docs/RELEASE.md`. Excluye `generator/`, `tools/`, `templates/`, `questionnaire/`, `bin/tests/`, `.github/` (meta-repo, no runtime del plugin instalado).
5. **Repo público** — `javiAI/pos-marketplace` no existe a fecha de F4. La infra local (`marketplace.json` + `release.yml` con mirror gated) está lista; el repo se crea manualmente cuando se decida ir live (runbook en [docs/RELEASE.md § Mirror al marketplace público](RELEASE.md)).

**Determinismo del release**:

- Drift `marketplace.json` ↔ `plugin.json` se rompe en CI vía `bin/tests/test_marketplace_json_schema.py` (cruza `name`, `version`, `source.ref`).
- Drift `plugin.json.version` ↔ tag git se rompe en `version-match` (primer job; sin esto el resto no corre).
- Bundle determinista: lista de paths fija; reordering en `release.yml` rompe contract test `test_release_workflow_smoke.py`.
- Pre-1.0 (`0.x`): API puede romper entre minors. F4 pinea `0.1.0`. `1.0.0` requiere decisión explícita.

**Instalación user-facing** (cuando el repo público exista):

```text
/plugin marketplace add javiAI/pos-marketplace
/plugin install pos
```

**Diferidos en F4** (regla #7 CLAUDE.md):

- `audit.yml` nightly (declarado en `policy.yaml.ci_cd.workflows` desde Fase A; sin consumer activo).
- Skills `/pos:pr-description` y `/pos:release` (sin repetición demostrada del flow manual).
- `CHANGELOG.md` enforced (autogenerated notes de `gh release create` cubren hasta nueva señal).
- Migración del `templates/policy.yaml.hbs` — cerrada en `refactor/template-policy-d5b-migration` post-F4 (era ortogonal a F4).

## 14. Anti-legacy / evolución

Cuando una fase supersede decisiones previas, esta sección declara qué queda obsoleto:

- `master_repo_blueprint.md` — referencia histórica. NO copiar. Este documento es verdad actual.

(Esta sección crece con cada fase mayor.)

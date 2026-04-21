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

## 1.1. Knowledge plane (opcional)

> **Opcional.** Capa extra mountable *dentro* del repo generado, adoptable vía opt-in del questionnaire. Introducida como roadmap en [MASTER_PLAN.md § FASE G](../MASTER_PLAN.md); no implementada todavía.

```
┌────────────────────────────────────────┐
│  META-REPO (control plane)             │
└───────────────┬────────────────────────┘
                │ genera
                ▼
┌────────────────────────────────────────┐
│  REPO GENERADO (runtime plane)         │
│                                        │
│  [opcional] vault/ (knowledge plane):  │
│    raw/       fuentes inmutables       │
│    wiki/      síntesis (LLM + humano)  │
│    schema.md  configuración            │
└────────────────────────────────────────┘
```

**Tres capas separadas** (terminología adaptada del [gist de Karpathy sobre wikis LLM-friendly](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)):

- `vault/raw/` — fuentes inmutables (artículos, papers, notas importadas, clippings). No se reescriben; se añaden.
- `vault/wiki/` — síntesis mantenida por LLM o humano. Cross-referenced, git-diffable.
- `vault/schema.md` — documento de configuración de la instancia: convenciones, reglas de síntesis, mapa de categorías.

**Principios invariantes**:

- **File-based**: todo es Markdown plano. Sin DB, sin formato propietario. Compatible con cualquier editor Markdown.
- **Tool-agnostic**: no impone cliente editor. Obsidian + Web Clipper es el **primer reference adapter** previsto — ver [MASTER_PLAN.md § Rama G2](../MASTER_PLAN.md). Logseq, Foam y plain-text son compatibles por construcción.
- **Opt-in**: el questionnaire declara `integrations.knowledge_plane.enabled` (shape final en G1). Con flag off, `vault/` no se emite.
- **Sin runtime compartido**: el knowledge plane vive en el repo generado, no en el meta-repo. El generador sólo emite el esqueleto; el mantenimiento es local al proyecto destino.

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

## 5. Skills (plugin namespace `pos:`)

Ver `.claude/rules/skills-map.md` para mapa completo con modelo + contexto.

### Principio `context: fork`

Skills con análisis pesado (`/pos:compound`, `/pos:audit-*`, `/pos:pre-commit-review`, `/pos:simplify`) corren en subagente aislado:

```yaml
context: fork
agent: code-reviewer   # agents/code-reviewer.md
model: claude-sonnet-4-6
effort: high
```

El agente recibe solo el payload necesario. Devuelve un report estructurado al context principal. Ahorro: 20-40k tokens por invocación.

### Sustituciones soportadas

`$ARGUMENTS`, `$1..$N`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_SKILL_DIR}`, `` !`command` `` (shell injection, requiere `shell: true` en frontmatter).

## 6. Agents (subagents)

- `agents/code-reviewer.md` — review de diffs.
- `agents/architect.md` — decisiones arquitectónicas (branch-plan, deep-interview, compound).
- `agents/auditor.md` — audit de plugins, policy check, session audit.

Cada agent declara sus tools permitidas (`allowed-tools:`) — subset mínimo. Un agente reviewer no debe tener `Write`. Un auditor no debe tener `Bash(git push)`.

## 7. Determinismo — tres capas

### Capa 1: Hooks (unchallengeable)

Código Python/bash. Exit code 2 = bloqueo. El LLM no puede ignorarlos. Son el último recurso de enforcement.

**Dos variantes canónicas** según el evento:

- **Blocker** (PreToolUse / PreCompact / Stop): safe-fail estricto — payload malformado → `deny` + exit 2 + `decisionReason`. El hook no puede dejar pasar lo que no puede validar. Referencia: `hooks/pre-branch-gate.py` (D1).
- **Informative** (SessionStart): safe-fail graceful — nunca emite `permissionDecision`, nunca exit 2. Payload malformado → `additionalContext` mínimo + entrada en `session-start.jsonl` vía `_log_error` (no se escribe a `phase-gates.jsonl`). Errores de git/subprocess → `additionalContext` mínimo + `_log_snapshot` sigue emitiendo la entrada happy-path (`branch=None`, `phase="unknown"`) en ambos logs; lo que se omite es la entrada de *error* (absorbidos por `_git` como `None`, sin `_log_error`). Fallos del propio logging (disk full, read-only fs) se tragan vía `_safe_append`. Exit 0 siempre. Bloquear un evento informativo dejaría al usuario sin contexto sin ganancia de enforcement. Referencia: `hooks/session-start.py` (D2).

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

**Helpers compartidos — `hooks/_lib/`** (extraído en D2 tras segunda repetición, CLAUDE.md regla #7):

- `_lib/slug.py::sanitize_slug` (`/` → `_`).
- `_lib/jsonl.py::append_jsonl` (append-only JSONL).
- `_lib/time.py::now_iso` (UTC ISO-8601).
- Consumidos desde hooks con nombre hyphenated via `sys.path.insert(0, str(Path(__file__).parent))` + `from _lib.X import Y  # noqa: E402` (sin convertir el hook a package formal). Las ramas D3..D6 deben reusar estos helpers en lugar de redefinir; añadir a `_lib/` sólo cuando ≥2 hooks usen el nuevo helper.

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
- Selftest (`bin/pos-selftest.sh`): escenarios end-to-end con proyecto sintético.
- Coverage gate (threshold de `policy.yaml.testing.unit.coverage_threshold`).

Hook `pre-push.sh` corre todos antes de permitir `git push`.

### CI (GitHub Actions)

Mismo set que local + matriz (2 OS × 2 versiones runtime). Branch protection requiere todos verdes para merge a main.

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

## 13. Marketplace público (Fase F4)

Repo `javiAI/pos-marketplace`:
- `marketplace.json` — lista de plugins publicados con versión + SHA.
- Release flow: tag `v*` en `project-operating-system` → workflow publica + abre PR en `pos-marketplace`.
- Users instalan con `claude plugin add javiAI/pos-marketplace::pos@X.Y.Z`.

Local sigue funcionando con `--plugin-dir <path>`.

## 14. Anti-legacy / evolución

Cuando una fase supersede decisiones previas, esta sección declara qué queda obsoleto:

- `master_repo_blueprint.md` — referencia histórica. NO copiar. Este documento es verdad actual.

(Esta sección crece con cada fase mayor.)

# MASTER_PLAN — project-operating-system

> Fuente de verdad ejecutable. Cada rama tiene scope fijo, Fase -1, criterio de salida. No añadir scope a ramas en vuelo — o se refina el plan o se crea rama nueva.

## §1. Convenciones

- **Slug de rama**: `<tipo>/<fase-id>-<nombre-corto>` — ej. `feat/a-skeleton`, `feat/d1-hook-branch-gate`.
- **Marker de aprobación**: `.claude/branch-approvals/<slug-sanitized>.approved`. Sanitized = slashes → underscores.
- **Kickoff block**: primer commit de cada rama, bloque `## Kickoff` con: scope, archivos, risks, test plan, docs plan. Hook lo valida.
- **PR target**: `main`. No feature branches de >5 días sin razón documentada.

## §2.1 Fase -1 (gate, obligatoria)

Antes de crear rama, emitir:

1. **Resumen técnico** (≤300 palabras): qué archivos tocamos, qué librerías añadimos, qué hooks/skills entran, qué tests.
2. **Resumen conceptual** (≤150 palabras): por qué esta rama ahora, qué desbloquea, qué NO incluye.
3. **Ambigüedades** (lista): cualquier duda ≥10% de incertidumbre sobre scope o implementación.
4. **Alternativas evaluadas**: al menos 2, con por qué se descartaron.
5. **Test plan**: qué se testea unit, integration, selftest, CI.
6. **Docs plan**: qué archivos docs se actualizan dentro de la rama.

Esperar aprobación explícita del usuario. Con OK → crear marker + rama.

---

## FASE A — Skeleton & bootstrap

### Rama A — `feat/a-skeleton`

**Status**: ✅ COMPLETADA (esta misma sesión, pre-bootstrap)

**Scope**:
- `git init` + `.gitignore` + `README.md`
- `.claude-plugin/plugin.json`
- `CLAUDE.md` meta-repo (<200 líneas)
- `.claude/rules/*.md` (7 rules path-scoped)
- `.claude/settings.local.json`
- `policy.yaml`
- `MASTER_PLAN.md` (este archivo)
- `ROADMAP.md`, `HANDOFF.md`, `AGENTS.md`
- `docs/ARCHITECTURE.md`, `docs/SAFETY_POLICY.md`, `docs/TOKEN_BUDGET.md`, `docs/KNOWN_GOOD_MCPS.md`
- `.gitkeep` en dirs vacíos

**Excepción**: se ejecutó sin Fase -1 formal porque es el bootstrap que CREA la propia Fase -1. Todas las ramas subsiguientes la respetan.

**Criterio de salida**:
- `ls -la` muestra estructura completa.
- `CLAUDE.md` <200 líneas.
- `policy.yaml` parseable por YAML 1.2.
- `plugin.json` parseable por JSON schema.

---

## FASE B — Cuestionario + profiles + generador esqueleto

### Rama B1 — `feat/b1-questionnaire-schema` ✅ PR #1

**Scope**: `questionnaire/schema.yaml` + `questionnaire/questions.yaml` + tests schema (vitest). Sin generador todavía.

**Contexto a leer**:
- [docs/ARCHITECTURE.md § Cuestionario](docs/ARCHITECTURE.md#cuestionario)
- [.claude/rules/generator.md](.claude/rules/generator.md)

**Criterio de salida**: `npx tsx tools/validate-questionnaire.ts` valida ambos archivos. Tests >90% coverage.

### Rama B2 — `feat/b2-profiles-starter` ✅

**Scope**: `questionnaire/profiles/nextjs-app.yaml`, `agent-sdk.yaml`, `cli-tool.yaml`. Cada profile responde ~60% del cuestionario (parcial por diseño; omite los 3 campos user-specific). Añade `tools/lib/profile-validator.ts` + `tools/validate-profile.ts` (CLI) + fixtures valid/invalid + CI step `Validate profiles`.

**Ajuste vs plan original**: los fixtures viven en `tools/__fixtures__/profiles/` (no en `generator/__fixtures__/profiles/`) porque el generador no existe todavía. Consolidación diferida a B3 si aplica.

**Brechas conocidas** (diferidas a B3):

- `answer-value-not-in-array-allowlist` no se valida a nivel de instancia (ArrayField.values existe en schema).
- Campos `enum` con valor array/objeto emiten `answer-value-not-in-enum` en lugar de `answer-type-mismatch` (taxonomía imprecisa, reporting subóptimo).

**Criterio de salida**: los 3 profiles validan contra el schema de B1 (`npm run validate:profiles` exit 0). Fixtures válidos + inválidos cubren los 5 issue kinds del validator. Tests >90% coverage.

### Rama B3 — `feat/b3-generator-runner`

**Scope**: `generator/run.ts` (CLI entrypoint), `generator/lib/profile-loader.ts`, `generator/lib/schema.ts` (re-export desde `tools/lib/`), `generator/lib/validators.ts` (`completenessCheck`). Sólo runner + validación. Sin renderers aún.

**Ajuste vs plan original**: `generator/lib/token-budget.ts` **diferido**. Motivo: `questionnaire/schema.yaml` no declara `workflow.token_budget` todavía; implementar el checker sin campo que leer sería abstracción prematura (CLAUDE.md regla #7). Reintroducir en rama posterior cuando el schema añada el campo. Mismo patrón de diferimiento que las 2 brechas de B2.

**Ajuste en `generator/lib/schema.ts`**: re-exporta `parseSchemaFile` / `parseProfileFile` / `validateProfile` desde `tools/lib/` en lugar de duplicar los zod schemas. 3ª aplicación de pattern-before-abstraction (la 2ª fue `tools/lib/read-yaml.ts` en B2). Si aparece una 4ª aplicación que exija lógica generator-only, se bifurcará entonces.

**Flags diferidos**: `--out` y `--dry-run` se rechazan explícitamente con exit 2 + mensaje `flag --X not supported in B3; planned for C1`. Evita falsa sensación de funcionalidad mientras renderers no existen.

**Semántica de exit codes**: profile con answers inválidos → exit 1; profile parcial con solo `identity.name`/`description`/`owner` faltantes → exit 0 + warning en stdout dentro del reporte (son user-specific, se resuelven en runner interactivo de fase posterior); otros required-missing → exit 1; I/O o args → exit 2.

**Criterio de salida**: `npx tsx generator/run.ts --profile ... --validate-only` retorna 0/1 según validez. Coverage 85%.

---

## FASE C — Templates + renderers

### Rama C1 — `feat/c1-renderers-core-docs`

**Scope**: renderers para `CLAUDE.md`, `MASTER_PLAN.md`, `ROADMAP.md`, `HANDOFF.md`, `AGENTS.md`, `README.md`. Templates Handlebars correspondientes. Snapshot tests + tests semánticos por renderer. Pipeline `FileWrite[]` + wire-up de `--out`/`--dry-run` en [generator/run.ts](generator/run.ts).

**Contexto a leer**:

- [docs/ARCHITECTURE.md § Generador](docs/ARCHITECTURE.md)
- [.claude/rules/generator.md](.claude/rules/generator.md) + [.claude/rules/templates.md](.claude/rules/templates.md)
- `generator/run.ts` + `generator/lib/` entregados en B3.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **User-specific placeholders**: los campos `identity.name|description|owner` faltantes en el profile no bloquean el render. El renderer inyecta literal `TODO(identity.<campo>)` + warning. Aplica tanto a `--dry-run` como a `--out`. Sustitución final pasará por el runner interactivo de fase posterior.
- **Carry-over Fase N+7 parcial**: en C1 solo cubre `templates/HANDOFF.md.hbs` (matriz de decisión + checklist post-merge) y `templates/AGENTS.md.hbs` (Fase N+7 en flujo de rama). `templates/.claude/rules/docs.md.hbs` **diferido a C2** por coherencia con el scope de C2 (`.claude/rules/*.md`).
- **`--out` con subdirectorios** desde el primer día. El pipeline trabaja con `FileWrite.path` relativo + `mkdir -p` — evita refactor en C2..C5.
- **`FileWrite` shape mínimo**: `{ path: string; content: string }`. Sin `mode`. Los bits de permisos se añaden en C5 (`feat/c5-renderers-skills-hooks-copy`) cuando la copia de hooks ejecutables los requiera.
- **`render-pipeline`** falla explícitamente ante colisión de paths (no sólo lo detecta en tests). Invariante: cada `path` del `FileWrite[]` combinado es único.
- **Snapshots + tests semánticos**: snapshots por (profile × template) = 18, pero además tests unitarios por renderer verifican paths emitidos y strings críticas (ej. "Fase N+7" en HANDOFF, "Kickoff block" en CLAUDE). Snapshots no son la única red de seguridad.
- **`--validate-only`** conservado por compat/transición. Sin flags = comportamiento validate-only. `--force` queda fuera de scope C1.

**Deps nuevas**: `handlebars` (única).

**Criterio de salida**: `npx tsx generator/run.ts --profile <canonical> --out <tmpdir>` emite el árbol esperado de 6 docs + placeholders visibles cuando aplique. `--dry-run` lista paths sin tocar fs. Snapshots estables (re-run byte-equal). Coverage ≥85%. CI verde.

### Rama C2 — `feat/c2-renderers-policy-rules` ✅

**Scope**: renderer para `policy.yaml` + `.claude/rules/*.md` (según stack/paths del profile). Templates + helpers Handlebars.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Composición de renderers en `generator/renderers/index.ts`, no en `run.ts`**: estructura con tres arrays congelados (`coreDocRenderers` + `policyAndRulesRenderers` + `allRenderers`). `run.ts` importa sólo `allRenderers` y permanece fino; futuras ramas (C3, C4, C5) crean array propio y lo componen dentro de `allRenderers` sin tocar `run.ts`. Evita que el runner se convierta en sitio de composición creciente.
- **Scope de rules acotado a `docs.md` + `patterns.md`**: no se incluyen `generator.md` / `templates.md` / `tests.md` / `ci-cd.md` / `skills-map.md`. Se añadirán en ramas posteriores sólo si aparece señal de stack-specificidad real.
- **`policy.yaml` por un solo renderer con un solo template Handlebars**: no se fragmenta por secciones. Conditionals stack inline (`{{#if (eq answers.stack.language "typescript")}}`) cubren `pre_push.checks_required` y `testing.unit.framework_node|framework_python`.
- **`type: "generated-project"` hardcoded** en el template (nunca depende del profile). **`project:` vía `{{answers.identity.name}}`** — expande a `TODO(identity.name)` mientras los 3 paths user-specific no estén resueltos (patrón heredado de C1).
- **Carry-over Fase N+7 cerrado**: `templates/.claude/rules/docs.md.hbs` incluye el bullet "Trazabilidad de contexto" referenciando `HANDOFF.md §3` (diferido desde C1 por coherencia de scope con `.claude/rules/*.md`).
- **Comentarios decorativos preservados** en `policy.yaml.hbs` (separadores `─` y cabeceras de sección). El render final mantiene la legibilidad del policy canónico del meta-repo.

**Deps nuevas**: ninguna (reuso de `handlebars` + `yaml` ya presentes).

**Criterio de salida** (cumplido): 9 `FileWrite` por profile (6 docs C1 + `policy.yaml` + `.claude/rules/docs.md` + `.claude/rules/patterns.md`), `yaml.parse(policy.yaml)` OK sobre los 3 canónicos, stack conditionals mutuamente exclusivos (no leaks), 27 snapshots (3 profiles × 9 templates) byte-estables entre runs, coverage ≥85%, CI verde.

### Rama C3 — `feat/c3-renderers-tests-harness`

**Scope**: renderer para test harness según stack (Node/Python/Go/Rust). Configs (vitest, jest, pytest, cargo, go.mod), README de tests, ejemplo smoke test.

### Rama C4 — `feat/c4-renderers-ci-cd`

**Scope**: renderer para `.github/workflows/*.yml` (+ GitLab/Bitbucket variants). Workflows coinciden con checks locales. Branch protection doc.

### Rama C5 — `feat/c5-renderers-skills-hooks-copy`

**Scope**: renderer que copia `skills/` + `hooks/` del plugin al proyecto generado, ajustando paths y permisos.

---

## FASE D — Hooks (Python)

### Rama D1 — `feat/d1-hook-pre-branch-gate`

**Scope**: `hooks/pre-branch-gate.py` + tests. Bloquea `git checkout -b` / `git switch -c` sin marker.

**Referencia**: ver [master_repo_blueprint.md](master_repo_blueprint.md) y el homólogo del repo de referencia (mentalmente; NO copiar literal).

### Rama D2 — `feat/d2-hook-session-start`

**Scope**: `hooks/session-start.py` — snapshot 30s (rama actual, último merge, fase en curso, warnings).

### Rama D3 — `feat/d3-hook-pre-write-guard`

**Scope**: `hooks/pre-write-guard.py` — enforza test-pair, inyecta patterns path-scoped, bloquea anti-patterns.

### Rama D4 — `feat/d4-hook-pre-pr-gate`

**Scope**: `hooks/pre-pr-gate.py` — valida policy.yaml vs logs: docs-sync, skills required, CI dry-run, invariants.

### Rama D5 — `feat/d5-hook-post-action-compound`

**Scope**: `hooks/post-action.py` — detecta merge, lee `policy.yaml.lifecycle.post_merge.skills_conditional`, dispara `/pos:compound` si trigger match (touched_paths).

### Rama D6 — `feat/d6-hook-pre-compact-stop`

**Scope**: `hooks/pre-compact.py` (persist decisions) + `hooks/stop-policy-check.py` (valida skill invocations vs policy).

---

## FASE E1 — Skills orquestación

### Rama E1a — `feat/e1a-skill-kickoff-handoff`

**Scope**: `skills/kickoff/`, `skills/handoff-write/`. Ambas `context: main`, sonnet.

### Rama E1b — `feat/e1b-skill-branch-plan-interview`

**Scope**: `skills/branch-plan/`, `skills/deep-interview/`. Ambas `context: fork`, opus.

---

## FASE E2 — Skills calidad

### Rama E2a — `feat/e2a-skill-review-simplify`

**Scope**: `skills/pre-commit-review/`, `skills/simplify/`. Ambas `context: fork`, sonnet.

### Rama E2b — `feat/e2b-skill-compress-audit-plugin`

**Scope**: `skills/compress/` (haiku, fork), `skills/audit-plugin/` (sonnet, fork). Este último implementa `docs/SAFETY_POLICY.md`.

---

## FASE E3 — Skills patrones + tests

### Rama E3a — `feat/e3a-skill-compound-pattern-audit`

**Scope**: `skills/compound/`, `skills/pattern-audit/`. Implementan el sistema de captura de patrones.

### Rama E3b — `feat/e3b-skill-test-scaffold-audit-coverage`

**Scope**: `skills/test-scaffold/`, `skills/test-audit/`, `skills/coverage-explain/`.

---

## FASE F — Audit + release + marketplace

### Rama F1 — `feat/f1-skill-audit-session`

**Scope**: `skills/audit-session/` — compara policy.yaml vs logs.

### Rama F2 — `feat/f2-agents-subagents`

**Scope**: `agents/code-reviewer.md`, `agents/architect.md`, `agents/auditor.md` — subagent definitions.

### Rama F3 — `feat/f3-selftest-end-to-end`

**Scope**: `bin/pos-selftest.sh` + escenarios. Valida todos los gates con proyecto sintético.

### Rama F4 — `feat/f4-marketplace-public-repo`

**Scope**: crear repo `javiAI/pos-marketplace` con `marketplace.json` + release flow. Docs en `docs/RELEASE.md`.

---

## §3. Progreso por fase

Mantenido en [ROADMAP.md](ROADMAP.md). No duplicar estado aquí.

## §4. Reglas de refinamiento

- Si una rama descubre scope que no estaba en Fase -1 → parar, anotar en kickoff, pedir guía. No extender rama silenciosamente.
- Si un criterio de salida no se puede cumplir → volver a Fase -1 documentando el obstáculo real.
- Ramas se abren en orden salvo que dos no tengan dependencia (ej. C1..C5 parcialmente paralelizables — evaluado caso por caso).

## §5. Ramas bloqueadas / condicionales

Ninguna en la planificación inicial. Cualquier blockeo se documenta aquí con `**BLOCKED**: <razón>`.

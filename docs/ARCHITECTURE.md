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

### Profiles predefinidos (Fase B2)

- `nextjs-app` — Next.js 15 + Prisma + PostgreSQL + Vitest + Playwright.
- `agent-sdk` — Agent SDK + Python + pytest + uv.
- `cli-tool` — TypeScript CLI + oclif + vitest.

Extensible en `questionnaire/profiles/*.yaml`. El generador soporta override key-por-key.

### Schema DSL (entregado en B1)

El schema NO es JSON Schema. Es un DSL propio YAML declarativo, validado por [tools/lib/meta-schema.ts](../tools/lib/meta-schema.ts) usando zod.

**Razones para DSL propio**:

- Permite verificar coherencia cross-file (`questions[].maps_to` ↔ paths de `schema.yaml`) sin ecosistema externo.
- Más legible al editar a mano: secciones A-G con `fields[]` discriminados por `type` (`string | number | boolean | enum | array`), constraints inline (`required`, `default`, `pattern`, `min/max`, `values`).
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

### Entrypoint

`generator/run.ts`:

```ts
import { parseArgs } from "node:util";
import { loadProfile } from "./lib/profile-loader";
import { validateProfile } from "./lib/schema";
import { renderAll } from "./renderers";
import { writeAll } from "./lib/fs-writer";

const { values } = parseArgs({
  options: {
    profile: { type: "string", short: "p" },
    out: { type: "string", short: "o" },
    "dry-run": { type: "boolean" },
    "validate-only": { type: "boolean" },
  },
});

const profile = await loadProfile(values.profile!);
validateProfile(profile);  // zod, throws en invalid
if (values["validate-only"]) process.exit(0);

const files = await renderAll(profile);
await writeAll(files, values.out!, { dryRun: values["dry-run"] });
```

### Renderers

Un renderer por output. Función pura. Input: profile + templates. Output: `FileWrite[]`.

Lista: CLAUDE.md, MASTER_PLAN.md, ROADMAP.md, HANDOFF.md, AGENTS.md, README.md, policy.yaml, `.claude/rules/*.md`, skills/copy, hooks/copy, agents/copy, `.github/workflows/*.yml`, test harness (vitest.config, pytest.ini, etc.), fixtures smoke.

### Determinismo

Los renderers NO leen `Date.now()`, `Math.random()`, ni variables de entorno del host. Todo viene de `profile`. Un timestamp requerido: `profile.metadata.generatedAt` inyectado desde el CLI (o `null` en tests). Esto permite snapshot testing sin flakes.

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
- Coverage gate en CI usando threshold de `policy.yaml`.
- Branch protection documentada en `docs/BRANCH_PROTECTION.md` (aplicación manual en GitHub Settings).

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

# HANDOFF — quickref 30s

> Leer al arrancar sesión. Diseñado para llegar a "puedo ejecutar Fase -1 de la siguiente rama" en <1 minuto.

## 1. Snapshot

- Repo: `project-operating-system` (plugin `pos`).
- Rama actual: **F3 ✅ PR pendiente** (`feat/f3-selftest-end-to-end`, en revisión docs-sync). Anterior: **F2 ✅ PR #26** (mergeada). Siguiente: **F4 — `feat/f4-marketplace-public-repo`** (`javiAI/pos-marketplace` + release flow).
- F3 entregó: `bin/pos-selftest.sh` (wrapper bash mínimo) + `bin/_selftest.py` (orquestador stdlib Python) + `bin/tests/test_selftest_smoke.py` + `bin/tests/test_selftest_scenarios.py` (5 escenarios funcionales-críticos D1/D3/D4/D5/D6 sobre proyecto sintético generado real-time por `npx tsx generator/run.ts --profile cli-tool.yaml`). CI: nuevo job `selftest` (ubuntu × py 3.11) en `.github/workflows/ci.yml`. Sin Claude Code runtime, sin invocaciones reales de skills/agents. Suite: 829 passed + 1 skipped.
- F2 entregó: `agents/pos-code-reviewer.md` + `agents/pos-architect.md` (plugin subagents primitive-correct con namespace `pos-*`); flips de `pre-commit-review` y `compound` a los nuevos consumidores; 26 contract tests parametrizados (`agents/tests/test_agent_frontmatter.py`). **No** toca `policy.yaml` (`agents_allowed` diferido). `auditor` diferido (sin consumer real, regla #7).
- F1 entregó: `/pos:audit-session` (read-only advisory main-strict) — compara 3 superficies explícitas de `policy.yaml` (`skills_allowed`, `lifecycle.<gate>.hooks_required`, `audit.required_logs`) vs `.claude/logs/` reales; reporta drift candidates por bucket sin auto-fix. Policy: `skills_allowed` 13→14. Fase F abierta (3/4 ramas).
- Fuente de verdad ejecutable: [MASTER_PLAN.md](MASTER_PLAN.md).
- Estado vivo: [ROADMAP.md](ROADMAP.md).
- Arquitectura canonical: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- **Horizonte post-F4**: Fase G (Knowledge Plane, opcional) planificada sin fecha — ver [MASTER_PLAN.md § FASE G](MASTER_PLAN.md).

## 2. Verificación de estado (1 comando)

```bash
git log --oneline -10 && git status -sb && ls .claude/branch-approvals/
```

Qué deberías ver:

- Último commit: cierre de la rama anterior (merge commit o docs-sync final).
- Working tree limpio.
- `.claude/branch-approvals/` con el marker de la rama en curso (si hay) o vacío.

Si el ROADMAP no coincide con `git log` → ROADMAP desfasado, actualizarlo antes de arrancar.

## 3. Decisión `/clear` vs `/compact` vs sesión nueva (Fase N+7 Context gate)

**Última fase de la rama anterior**, ejecutada post-merge / post-`/pos:compound`. Puerta de entrada obligatoria a Fase -1 de la siguiente rama. AGENTS.md regla #1.

| Caso | Acción |
|---|---|
| Rama anterior mergeada, docs + memoria al día | `/clear` |
| Fase -1 de siguiente rama hecha en esta sesión, sin persistir | `/compact keep_recent_messages=50` + guardar decisiones como memoria `project` |
| Sesión larga con decisiones sin grabar | `/compact focus="decisiones pendientes"` + memorias `project` |
| Cambio de rama ortogonal | Sesión nueva (MEMORY.md + CLAUDE.md cargan solos) |

Regla dura: contexto crítico NO en git + docs + memoria → **NO `/clear`**. Persiste primero.

### Checklist pre-Fase-1

- [ ] Evaluar contexto actual: ¿tamaño?, ¿decisiones sin grabar?, ¿rama previa cerrada en docs?
- [ ] **Claude presenta al usuario** las 4 opciones con recomendación razonada: `continuar` | `/compact focus="..."` | `/clear` | sesión nueva.
- [ ] **Parar. Esperar elección explícita del usuario.** Claude nunca decide la opción por su cuenta, ni siquiera cuando `continuar` parezca obvio.
- [ ] Si usuario elige `compact` / `clear` / sesión nueva: emitir **resume prompt** con:
  - Archivos a releer (MASTER_PLAN § rama + "Contexto a leer" + schema/rules relevantes).
  - Decisiones ya tomadas que deben sobrevivir (shape, alternativa elegida, ambigüedades resueltas).
  - Tareas pendientes dentro de la rama nueva.
- [ ] Solo tras la decisión explícita del usuario proceder con Fase -1 (§2.1 MASTER_PLAN.md).
- [ ] Si la siguiente rama se inicia con `/compact` o `/clear`, el primer commit de kickoff referencia el resume prompt (trazabilidad).

## 4. Orden óptimo de lectura al arrancar rama

1. Este archivo.
2. MEMORY.md (se carga solo).
3. **Sección entera de la rama** en MASTER_PLAN.md.
4. Archivos citados en "Contexto a leer" de la rama — sólo esos.
5. Ejecutar Fase -1 (ver MASTER_PLAN.md §2.1). Esperar aprobación del usuario.

**Anti-patrón**: leer MASTER_PLAN.md entero o `docs/ARCHITECTURE.md` completo cuando sólo necesitas una sección. Cita por rangos.

## 5. Template de prompt para continuar tras merge

```
Continúa con MASTER_PLAN.md.
Rama mergeada: ✅ [nombre-rama] (PR #N).
Siguiente rama: XY `feat/xy-nombre`.
Lee solo:
  - MASTER_PLAN.md § Rama XY
  - Archivos citados en "Contexto a leer" de esa rama
Ejecuta §2.1 Fase -1 completo. Espera aprobación explícita antes de `git checkout -b`.
```

## 6. Pre-flight checklist

- [ ] `git pull origin main --ff-only`
- [ ] `.env` no necesario en esta fase (no hay runtime todavía).
- [ ] Python 3.10+ disponible (`python3 --version`).
- [ ] Node 18+ disponible (`node --version`).
- [ ] `npx tsx --version` funcional.
- [ ] Fase -1 aprobada explícitamente.
- [ ] Marker creado: `.claude/branch-approvals/<slug-sanitized>.approved`.
- [ ] `git checkout -b feat/<rama>` tras el marker.

## 6b. Carry-over a fases futuras

- **C1 (`feat/c1-renderers-core-docs`)** ✅ [parcial completada]: Fase N+7 propagada en `templates/HANDOFF.md.hbs` (matriz + checklist) y `templates/AGENTS.md.hbs` (Fase N+7 como última fase del flujo de rama).
- **C2 (`feat/c2-renderers-policy-rules`)** ✅ **carry-over cerrado**: `templates/.claude/rules/docs.md.hbs` incluye el bullet "Trazabilidad de contexto" referenciando `HANDOFF.md §3`. Todo proyecto generado con `pos` hereda ya la disciplina completa de context-management.
- **C3 (`feat/c3-renderers-tests-harness`)** ✅ sin carry-over abierto. Frameworks diferidos (`jest`, `go-test`, `cargo-test`) quedan como fallo explícito dentro de `renderTests(...)` — se retomarán sólo cuando un profile canónico los adopte (≥1 repetición → reevaluar con regla #7 CLAUDE.md). `package.json` / `pyproject.toml` / `playwright.config.ts` diferidos también, documentados en el README emitido ("Qué NO emite C3").
- **C4 (`feat/c4-renderers-ci-cd`)** ✅ sin carry-over abierto. `gitlab` / `bitbucket` diferidos con `Error` explícito dentro de `ci-cd.ts` — mismo patrón que C3 (reabrir sólo si un profile canónico los adopta). `release.yml` / `audit.yml` diferidos a rama propia (ramas de `workflow.release_strategy` divergen). `stack.runtime_version` no existe en schema → Node 20.17.0 + Python 3.11 hardcoded en template C4; deuda documentada en `.claude/rules/generator.md § Deferrals`. Python toolchain mínimo (`pip install pytest pytest-cov`); adoptar `uv`/`poetry`/`pdm` se pospone hasta que C5/C6 emita `pyproject.toml`.
- **C5 (`feat/c5-renderers-skills-hooks-copy`)** ✅ **con carry-over abierto**. C5 cierra la *estructura* del directorio `.claude/` (3 archivos esqueleto por profile: `settings.json` + `hooks/README.md` + `skills/README.md`). **NO** implementa la *copia real* de hooks ejecutables ni de skills — eso queda diferido a la primera rama post-D1/E1a que necesite copiar artefactos reales. `FileWrite.mode` sigue diferido (C1–C5 usan `{ path, content }` sin `mode`); la extensión se abrirá en la misma rama que copie ejecutables. `settings.json` **no** siembra `permissions` baseline (decisión explícita: minimo conservador); esa decisión la tomará Fase D cuando los hooks reales definan su superficie.

## 7. Gotchas del entorno

- El hook `pre-branch-gate.py` **ya está vivo** desde D1: `git checkout -b`, `git switch -c` y `git worktree add -b` sin marker quedan bloqueados por exit 2 + `permissionDecision: deny`. El bypass legítimo es crear marker explícito.
- El hook `session-start.py` **ya está vivo** desde D2: imprime snapshot (branch, phase, last merge, warnings) como `additionalContext` en cada SessionStart (`startup` / `resume` / `clear` / `compact`). Informativo, nunca bloquea — errores de payload o git degradan a snapshot mínimo + log de error (exit 0 siempre).
- El hook `pre-write-guard.py` **ya está vivo** desde D3: PreToolUse(Write) blocker. Bloquea con exit 2 la creación de archivos en paths enforced (`hooks/*.py` top-level + `generator/**/*.ts` excluyendo tests/fixtures) sin test pair co-located. Los writes sobre archivos existentes en esos paths enforced sí pasan, pero siguen logueándose (allow / audit trail del flujo de edición). El pass-through silencioso (sin log) aplica solo a `hooks/_lib/**`, tests/docs/templates/meta y paths fuera del repo. Bypass legítimo: crear primero `hooks/tests/test_<x>.py` o `<path>.test.ts` con un test que falle (RED), luego escribir la implementación.
- El hook `pre-pr-gate.py` **ya está vivo** desde D4: PreToolUse(Bash) blocker sobre `gh pr create` únicamente. Resuelve base con `git merge-base HEAD main` y calcula archivos tocados con `git diff --name-only <base> HEAD`. Bloquea con exit 2 cuando ese diff no contiene los docs exigidos (required `ROADMAP.md` + `HANDOFF.md`; conditional por prefijo: `generator/**` | `hooks/**` excl. `hooks/tests/` | `.claude/patterns/**` → `docs/ARCHITECTURE.md`; `skills/**` → `.claude/rules/skills-map.md`). Skip advisory (pass-through + log explícito en hook log, no en phase-gates) en `main` / `master` / HEAD detached / cwd no-git / main borrada localmente / `git diff` subprocess falla (`diff_files() is None`). Empty diff (`[]`) → deny dedicado con reason `empty PR`, separado textualmente del reason docs-sync. 3 entradas advisory `deferred` (skills_required / ci_dry_run_required / invariants_check) se loguean en cada decisión real como scaffold activable sin cambio de shape cuando sus ramas dedicadas aporten sustrato. Reglas hardcoded (mirror de `policy.yaml.lifecycle.pre_pr.docs_sync_required` + `docs_sync_conditional`); divergencia deliberada D4: la lista `hooks/**` de la policy es uniforme, el hook excluye `hooks/tests/` — convergencia diferida a la rama policy-loader. Migración a parser declarativo en esa misma rama (junto con los paths hardcoded de D3).
- **Loader declarativo `hooks/_lib/policy.py`** vivo desde D5b: los tres hooks D3/D4/D5 ya **no** hardcodean policy — leen via `docs_sync_rules()` / `post_merge_trigger()` / `pre_write_rules()`. Failure mode canónico (c.2): `policy.yaml` ausente o corrupto → loader devuelve `None` → hook degrada a pass-through advisory con `status: policy_unavailable` en su propio log. Nunca deny blind. Consumo único (stdlib + `pyyaml==6.0.2`, primera dependencia no-stdlib en `hooks/_lib/`, justificada en kickoff D5b). Ver `.claude/rules/hooks.md § Policy loader`.
- **Drift temporal meta-repo ↔ template** abierto tras D5b: `policy.yaml` (meta-repo) tiene el shape nuevo (`pre_write.enforced_patterns` + `docs_sync_conditional.hooks/**` con `excludes: ["hooks/tests/**"]`); `templates/policy.yaml.hbs` y el renderer `generator/renderers/policy.ts` **no** — un proyecto generado hoy con `pos` emite un `policy.yaml` con el shape previo. Reconciliación diferida a rama propia post-D6 (update template + renderer + snapshots + `pyyaml` a requirements-dev de proyectos Python generados).
- El hook `post-action.py` **ya está vivo** desde D5: PostToolUse(Bash) hook **non-blocking** (exit 0 siempre; no emite `permissionDecision`). Detección jerárquica 2 tiers — Tier 1 (`shlex.split`): matcher A `git merge <ref>` (excluye `--abort/--quit/--continue/--skip`), matcher C `git pull` (excluye `--rebase/-r`). Tier 2 (`git reflog HEAD -1 --format=%gs`): confirma `"merge "` (A) o `"pull:" | "pull "` y no `"pull --rebase"` (C). `gh pr merge` (matcher B) descartado en Fase -1 por ausencia de `tool_response.exit_code` garantizado. Con ambos tiers confirmados: `git diff --name-only HEAD@{1} HEAD` + `fnmatch` contra `TRIGGER_GLOBS` mirror de `policy.yaml.lifecycle.post_merge.skills_conditional[0]` (`generator/lib/**`, `generator/renderers/**`, `hooks/**`, `skills/**`, `templates/**/*.hbs`), respetando `SKIP_IF_ONLY_GLOBS` (`docs/**`, `*.md`, `.claude/patterns/**`) y `MIN_FILES_CHANGED = 2`. Si matchea, emite `hookSpecificOutput.additionalContext` sugiriendo `/pos:compound` (4 líneas, cap 3 paths + `(+N more)`). **Nunca dispatcha la skill** — advisory-only; D5 sólo sugiere, E3a la entrega. Double log: `post-action.jsonl` (4 status distinguidos: `tier2_unconfirmed`, `diff_unavailable`, `confirmed_no_triggers`, `confirmed_triggers_matched`) + `phase-gates.jsonl` (evento `post_merge`, sólo en los dos status confirmed — los advisory tier2/diff no cruzan la puerta del lifecycle). Pass-throughs (Tier 1 no matchea) NO loguean. Reuso `_lib/`: `append_jsonl` + `now_iso`. Hardcode mirror de `policy.yaml` (segunda repetición tras D4) — regla #7 CLAUDE.md **cumplida dos veces** para el parser declarativo, precondición ready para la rama policy-loader.
- El hook `pre-compact.py` **ya está vivo** desde D6: PreCompact **informative** (shape D2) — exit 0 siempre, nunca `permissionDecision`. Lee `pre_compact_rules(cwd).persist` del loader (D5b) y emite `additionalContext` con checklist de items a persistir antes del compact. Failure mode canónico (c.2): policy ausente o sección `lifecycle.pre_compact` ausente → loader devuelve `None` → hook emite contexto informativo mínimo que señala policy no disponible + log `status: policy_unavailable`. Safe-fail informative ante stdin corrupto: contexto degradado que señala el error de payload + log `status: payload_error`. Double log: `pre-compact.jsonl` siempre; `phase-gates.jsonl` evento `pre_compact` **solo** en happy path. (Wording exacto del contexto no es contrato — no se citan strings; ver `hooks/pre-compact.py` y sus tests si algún consumidor necesita inspeccionarlo.)
- El hook `stop-policy-check.py` **ya está vivo** desde D6 como **scaffold activable** — shape D1 blocker (safe-fail canónico deny en payload malformado), pero **sin enforcement en producción hoy**. Lee `skills_allowed_list(cwd)` como tri-estado: `None` → `status: deferred` + pass-through silencioso (sección `skills_allowed` ausente del `policy.yaml` del meta-repo hoy); `SKILLS_ALLOWED_INVALID` → `status: policy_misconfigured` + pass-through (clave presente pero mal formada — **observable, NO silenciosa**: un typo en la policy ya no apaga enforcement como si fuera deferred); `()` → explicit deny-all; `tuple[str, ...]` poblada → enforcement live. Las invocaciones se leen de `.claude/logs/skills.jsonl` **filtradas por el `session_id`** del payload Stop actual (entradas de sesiones anteriores o sin `session_id` se ignoran); sin `session_id` en el payload → deny safe-fail (no se puede scopiar enforcement). Double log solo en decisiones reales (`deferred`/`policy_misconfigured`/`policy_unavailable` van solo al hook log, no cruzan `phase-gates.jsonl`). Framing **anti-sobrerrepresentación**: hoy el hook NO protege nada en producción; la entrega D6 aporta el shape y la suite de tests que valida el contrato — el switch-on real llega cuando una skill poblada declare su allowlist.
- `policy.yaml` declarado pero no enforced todavía (un-parseado). D4 (docs-sync) y D5 (compound trigger) mirror sus reglas de forma hardcoded; parser declarativo diferido a rama dedicada (precondición regla #7 ya cumplida por dos repeticiones).
- `/pos:*` skills no existen aún (Fase E*). Invocaciones fallarán silenciosas. Usar comportamiento manual equivalente.

### Deuda técnica abierta — schema defaults no materializados en `buildProfile`

Desde C3. `generator/lib/profile-model.ts::buildProfile` expande dotted-answers a nested e inyecta placeholders `TODO(identity.X)` para los 3 paths user-specific, pero **no lee `field.default` del schema**. Si un template referencia un path con `default:` declarado en `questionnaire/schema.yaml`, el profile debe declararlo explícitamente — en caso contrario el template renderiza `undefined` / vacío y el snapshot falla.

**Síntoma visible hoy**: `generator/__fixtures__/profiles/valid-partial/profile.yaml` añade `testing.coverage_threshold: 80` + `testing.e2e_framework: "none"` explícitos (no via default) porque los templates C3 los usan. Los 3 profiles canónicos (`nextjs-app`, `cli-tool`, `agent-sdk`) también los declaran explícitos.

**Impacto en próximas ramas**:

- **C4 (CI/CD)** — si los workflows usan `testing.coverage_threshold` u otros paths con default, los 3 canonicals + `valid-partial` deben declararlo explícito (mismo patrón que C3). No basta con añadir el campo al schema.
- **C5 (skills + hooks copy)** — mismo riesgo si alguna plantilla de policy.yaml o hook config referencia defaults.

**Resolución futura (rama propia)**: extender `buildProfile` para leer `field.default` del schema y materializarlo cuando el profile no declare el path. Cuando se aborde, eliminar también los campos redundantes de los 3 canonicals + `valid-partial`. Scope diferido deliberadamente en C3 para no mezclar alcance.

Ver detalle: `.claude/rules/generator.md` (Deferrals), `MASTER_PLAN § Rama C3` (Ajustes), `ROADMAP § Progreso Fase C` (entregables).

## 8. Skills / subagents del entorno Claude Code (no plugin)

Hasta F1 el plugin reusaba subagents built-in; desde F2 los críticos son propios:

- `pos-code-reviewer` (plugin, F2) — consumido por `pre-commit-review`. Fallback `general-purpose` si runtime no expone agents del plugin.
- `pos-architect` (plugin, F2) — consumido por `compound`. Fallback `general-purpose`.
- Built-in residuales (sólo si `branch-plan` requiere lectura ≥3 archivos): `Plan`, `Explore`, `code-architect`. Mismos fallback rules.
- Skills globales del usuario (si las tiene en `~/.claude/skills/`).

## 9. Próxima rama

**F4 — `feat/f4-marketplace-public-repo`** (tras merge de F3 — última rama de Fase F: marketplace público + release flow).

Scope:

- Crear repo `javiAI/pos-marketplace` con `marketplace.json` + release flow.
- Docs en `docs/RELEASE.md`.
- Workflow `.github/workflows/release.yml` (en tag `v*`): valida versión `plugin.json` = tag, publica release con assets, actualiza `pos-marketplace` vía PR automático.
- Decisión Fase -1: ¿shape de `marketplace.json`?, ¿cómo se versiona el plugin (`plugin.json` vs git tag)?, ¿qué assets entran en el release bundle?, ¿`audit.yml` nightly entra aquí o se difiere a una rama post-F4?

## 10. Estado E2b (✅ merged PR #22)

Entregables completados:

- `/pos:compress`: read-only advisory planner. Propone compresión de `.claude/logs/*.jsonl` (edad, tamaño, importancia). User decides ejecución. Logging best-effort.
- `/pos:audit-plugin`: read-only advisory gate. Audita community tools contra SAFETY_POLICY.md 6-item checklist. Retorna GO/NO-GO/NEEDS_MORE_INFO. No instala, no enforza, no modifica policy. E2b advisory-only (enforcement deferred).
- Policy: `skills_allowed` extendido 6→8 (compress, audit-plugin).
- Tests: parametrizados (8 skills) + behavior contracts (STOP signal, advisory keywords locked).
- Docs: MASTER_PLAN § E2b (decisiones A1a-A5a ratificadas) + ROADMAP (✅) + HANDOFF (actualizado) + skills-map.md (descripción final).

## 11. Estado D5 (cerrada en rama)

`post-action` vivo: en cada `PostToolUse(Bash)` aplica detección jerárquica 2 tiers. Tier 1 (`shlex.split`): matcher A `git merge <ref>` excluyendo flags de control `--abort/--quit/--continue/--skip`; matcher C `git pull` excluyendo `--rebase`/`-r`. Tier 2 (`git reflog HEAD -1 --format=%gs`): confirma `"merge "` (A) o `"pull:" | "pull "` sin `"pull --rebase"` (C) — evita disparar en `git merge --abort` o en pulls rebase-sin-flag. `gh pr merge` (matcher B) descartado en Fase -1 por ausencia de `tool_response.exit_code` garantizado en PostToolUse(Bash). Con ambos tiers confirmados: `git diff --name-only HEAD@{1} HEAD` + `fnmatch` contra `TRIGGER_GLOBS` / `SKIP_IF_ONLY_GLOBS` / `MIN_FILES_CHANGED=2` (mirror literal de `policy.yaml.lifecycle.post_merge.skills_conditional[0]`). Match → emite `additionalContext` sugiriendo `/pos:compound` (4 líneas, cap 3 paths + `(+N more)`); nunca dispatcha la skill (D5 advisory-only, E3a entrega la skill real). Exit 0 siempre — PostToolUse non-blocking (ni `permissionDecision` ni exit 2 bajo ningún camino). Double log: `post-action.jsonl` con 4 status (`tier2_unconfirmed`, `diff_unavailable`, `confirmed_no_triggers`, `confirmed_triggers_matched`) + `phase-gates.jsonl` evento `post_merge` sólo en los dos status confirmed — los advisory tier2/diff no cruzan la puerta del lifecycle. Pass-through (Tier 1 miss) silencioso (cero log, replica D1). 111 tests D5 (110 passed + 1 skip intencional — delegación interna entre integración y unit), 432 totales en `hooks/**`, 97% coverage sobre `post-action.py`; D1/D2/D3/D4 intactos. Hardcode de `policy.yaml` es la **segunda repetición tras D4** — regla #7 CLAUDE.md cumplida dos veces, precondición abierta para la rama policy-loader.

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § feat/d5](ROADMAP.md), [MASTER_PLAN.md § Rama D5](MASTER_PLAN.md) y [.claude/rules/hooks.md § Quinto hook](.claude/rules/hooks.md).

## 12. Estado D5b (cerrada en rama)

`refactor/d5-policy-loader` — sub-rama que cumple la precondición CLAUDE.md regla #7 abierta por D4 + D5 (dos repeticiones hardcoded de `policy.yaml`). Entrega `hooks/_lib/policy.py` como **fuente única de verdad para los hooks D3/D4/D5** y migra los tres consumidores en el mismo PR.

**Shape del loader**: 5 dataclasses congeladas (`ConditionalRule`, `DocsSyncRules`, `PostMergeTrigger`, `EnforcedPattern`, `PreWriteRules`) + `load_policy(repo_root)` cacheado (clave: path abs **únicamente** — sin mtime/size, sin invalidación implícita por edits al archivo dentro del mismo proceso; `reset_cache()` para test isolation o relectura controlada. En la práctica los hooks CLI arrancan proceso nuevo y recargan así; este handoff NO debe leerse como si hubiese hot-reload por cambios on-disk) + 3 accessors tipados (`docs_sync_rules` / `post_merge_trigger` / `pre_write_rules`, cada uno devuelve `None` si policy.yaml falta o la sección relevante no existe) + `derive_test_pair(rel_path, label)` con dos ramas label-driven (`hooks_top_level_py` + `generator_ts`). Decisión (b.1) Fase -1: strings/globs viven en YAML, derivación procedural vive en Python — NO YAML DSL.

**Failure mode canónico (c.2)**: `policy.yaml` ausente o corrupto → loader devuelve `None` → cada hook consumidor degrada a **pass-through advisory** con entrada `status: policy_unavailable` en su propio log. Nunca deny blind. Ver implementación de referencia en `pre-pr-gate.main()` tras `docs_sync_rules(repo_root)` y `post-action.main()` tras `post_merge_trigger(repo_root)`. Esta es la decisión que cierra la alternativa "deny defensivo" (brickearía PRs ante un typo YAML) y "fallback hardcoded" (rompería el propósito de tener loader).

**Cambios no-loader en `policy.yaml`**:

- Nuevo bloque `pre_write.enforced_patterns` (3 entries — `hooks_top_level_py` + `generator_ts` × 2, dos entries con la misma label keyed por `match_glob` distinto porque `fnmatch.fnmatchcase("generator/run.ts", "generator/**/*.ts")` no matchea — el middle `/` de `**` es literal en fnmatch; workaround documentado en § Ajustes de ROADMAP D5b).
- `lifecycle.pre_pr.docs_sync_conditional.hooks/**` ahora con `excludes: ["hooks/tests/**"]`. **Divergencia deliberada D4 cerrada**: policy + hook ya son fuente única coherente.

**Drift temporal meta-repo ↔ template** (explícito — no leer como "template ya refleja el nuevo shape"): `templates/policy.yaml.hbs` + `generator/renderers/policy.ts` **NO tocados** en esta rama. Proyectos generados hoy con `pos` emiten un `policy.yaml` con el shape previo (sin `enforced_patterns`, sin `excludes` en `hooks/**`). Reconciliación diferida a rama propia post-D6 (update template + renderer + snapshots + `pyyaml` en requirements-dev de proyectos Python generados). Documentado también en ROADMAP §D5b, MASTER_PLAN § Rama D5b y ARCHITECTURE §7.

**Dependencia**: primera línea no-stdlib en `hooks/_lib/` — `pyyaml==6.0.2` (pin exacto) añadida a `requirements-dev.txt`. Justificación en kickoff D5b: no hay parser YAML en stdlib Python, escribir uno a mano sobre nuestro `policy.yaml` sería código muerto (mantenemos un bindings YAML bien soportado).

**Migración de los 3 hooks** (mismo PR):

- `pre-write-guard.py` — `classify(rel_path, rules)` recorre `rules.enforced_patterns` con `fnmatch.fnmatchcase`; derivación via `derive_test_pair(rel_path, label)`. Los dos buckets de exclusión (tests/docs/templates/meta vs helper internals `_lib/**`) siguen inmutables — son pass-through silencioso, no migran a YAML (sería abstracción prematura).
- `pre-pr-gate.py` — `check_docs_sync(files, rules)` + `_conditional_triggers(files, rules)` leen de `DocsSyncRules`. Shape blocker D1 intacto; advisory scaffold intacto.
- `post-action.py` — `match_triggers(paths, trigger)` lee de `PostMergeTrigger`. Tier 1/Tier 2 detection intacta; sólo cambia la fuente de los globs.

**Resultado**: 462 tests verdes + 1 skip intencional (sin regresión); `_lib/policy.py` coverage 97%; `pre-write-guard.py` 93%, `pre-pr-gate.py` 93%, `post-action.py` 94%. Suite `hooks/**` engordada con `test_lib_policy.py` (57 casos) y adelgazada de `TestIsEnforcedUnit`/`TestExpectedTestPairUnit` en D3 (~23) + `TestPolicyConstants` en D5 (3) — redundantes con el loader test.

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § refactor/d5-policy-loader](ROADMAP.md), [MASTER_PLAN.md § Rama D5b](MASTER_PLAN.md), [.claude/rules/hooks.md § Policy loader](.claude/rules/hooks.md) y [docs/ARCHITECTURE.md § 7](docs/ARCHITECTURE.md).

## 13. Estado D6 (cerrada en rama, docs-sync en curso)

`feat/d6-hook-pre-compact-stop` — sexto y séptimo hook Python, cierre de Fase D antes de arrancar Fase E (skills). Dos entregas en un PR deliberadamente (decisión Fase -1 "both-together"): ambos hooks comparten el mismo nuevo accessor pattern sobre el loader D5b (`pre_compact_rules` + `skills_allowed_list`) y se testean contra el mismo fixture set — separarlos habría generado churn sin beneficio.

**`hooks/pre-compact.py` — PreCompact informative (shape D2, no-enforcement)**: lee `pre_compact_rules(cwd).persist` y emite una checklist en `additionalContext` antes de que Claude Code haga `/compact`. Exit 0 siempre; nunca `permissionDecision`. Happy path: header + bullet list de items a persistir (patrones, decisiones, marker files). Failure mode canónico (c.2): policy ausente o `lifecycle.pre_compact` ausente → `build_context` informativo minimal + log `status: policy_unavailable`. Safe-fail informative ante stdin corrupto: contexto degradado que señala el error + log `status: payload_error` — el hook nunca rompe el compact, sólo degrada su contexto. El wording exacto del `additionalContext` **no es contrato** (no lo citamos aquí): consultar `hooks/pre-compact.py` + `hooks/tests/test_pre_compact.py` si algún consumidor necesita inspeccionarlo. Double log: `pre-compact.jsonl` siempre; `phase-gates.jsonl` evento `pre_compact` **solo** en happy path (policy_unavailable y payload_error no cruzan la puerta del lifecycle).

**`hooks/stop-policy-check.py` — Stop blocker scaffold (shape D1, NO enforcement en producción hoy)**: este es el punto de framing más importante de D6. Hoy el hook está **activable pero desactivado**: `policy.yaml` no declara `skills_allowed`, así que `skills_allowed_list(cwd)` devuelve `None` y el hook entra en camino `status: deferred` — exit 0, pass-through silencioso. Cuando E1a declare una skill real y pueble `skills_allowed`, el hook **ya está listo sin cambio de código**: lee `.claude/logs/skills.jsonl` filtrando por el `session_id` del payload Stop actual via `_extract_invoked_skills`, compara contra la allowlist, y emite `permissionDecision: deny` + exit 2 si hay violación. Shape D1 canónico: safe-fail `_deny_payload` ante stdin malformado o `session_id` ausente/no-string (deny canónico, nunca allow blind — sin session_id no puede scopiarse enforcement). Contrato tri-estado de `skills_allowed_list`: `None` = sección ausente → `status: deferred`; `SKILLS_ALLOWED_INVALID` (sentinel) = presente pero mal formada → `status: policy_misconfigured` **observable** (NO colapsa con deferred — un typo en la policy no apaga enforcement silenciosamente); `()` = declarada vacía → deny-all explícito; tupla poblada = enforcement live. Session scoping: entradas de `skills.jsonl` con `session_id` distinto o ausente se ignoran (el log es append-only y acumula entre sesiones). Double log: solo en decisiones reales (deferred + policy_misconfigured + policy_unavailable van al hook log, no cruzan `phase-gates.jsonl`).

**Decisión anti-sobrerrepresentación (Fase -1)**: D6 entrega el shape + suite de tests + contrato, no enforcement. Documentación en MASTER_PLAN § Rama D6, `.claude/rules/hooks.md § Séptimo hook entregado`, y `docs/ARCHITECTURE.md § 7 (cuarta aplicación blocker — scaffold)` lo explicita: el hook "protege" en el sentido de que valida su propio shape y está listo; no en el sentido de que hoy impida ninguna skill (ninguna existe todavía).

**Consumo del loader**: dos accessors nuevos en `hooks/_lib/policy.py` (D5b + D6 = 5 accessors totales): `pre_compact_rules(repo_root) -> PreCompactRules | None` (nuevo dataclass `PreCompactRules(persist: tuple[str, ...])`) + `skills_allowed_list(repo_root) -> tuple[str, ...] | None | SkillsAllowedInvalid` (tri-estado explícito tras revisión PR — sentinel `SKILLS_ALLOWED_INVALID` separa "ausente" de "mal formada"). Ambos delegan a helpers internos del loader. Regla #7 CLAUDE.md respetada: dos consumidores nuevos, no un helper compartido prematuro.

**Resultado**: 575 tests verdes + 1 skip intencional (vs. 462+1 baseline D5b; +113 tests nuevos en D6 — 80 específicos de los dos hooks nuevos, 20 sobre loader extendido, 13 cobertura cruzada/session-scoping/misconfigured); `pre-compact.py` 89% coverage, `stop-policy-check.py` 89% coverage, `_lib/policy.py` extendido mantiene 97%. Hook suite completa sin regresión sobre D1..D5.

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § feat/d6-hook-pre-compact-stop](ROADMAP.md), [MASTER_PLAN.md § Rama D6](MASTER_PLAN.md), [.claude/rules/hooks.md § Sexto hook + Séptimo hook](.claude/rules/hooks.md) y [docs/ARCHITECTURE.md § 7](docs/ARCHITECTURE.md).

## 14. Estado E1a (cerrada en rama, docs-sync en curso)

`feat/e1a-skill-kickoff-handoff` — **primera rama de Fase E y primera entrega de Claude Code Skills reales** del meta-repo. Cierra la asimetría pre-E (hooks D vivos pero skills referenciadas en `skills-map.md` inexistentes → invocaciones fallaban silenciosas) y activa el scaffold Stop entregado en D6 sin tocar código del hook.

**Primitive correction — lección permanente**: Fase -1 v1 propuso `skill.json` + frontmatter extendido (`context:`, `model:`, `agent:`, `effort:`, `hooks:`, `user-invocable:`). Rechazado por el usuario y reemitido. El primitive oficial de Claude Code Skills es **exclusivamente** `.claude/skills/<slug>/SKILL.md` con frontmatter YAML mínimo: `name` + `description` + `allowed-tools` opcional. **No inventar campos** por analogía con slash commands; si un futuro release del SDK documenta nuevos campos, se citan con fuente antes de introducirlos. Ver la memoria local `feedback_skill_primitive_minimal.md` en el store de memoria del proyecto (indexada en `MEMORY.md`).

**Entregables**:

- `.claude/skills/project-kickoff/SKILL.md` — snapshot 30s. Reads `git log/status/rev-parse`, `ROADMAP.md` § ⏳ row, `HANDOFF.md` §1 + §9; emite ≤12 líneas (branch, phase, last merge, next branch, warnings). **STOPS BEFORE Fase -1** — no crea markers, no ejecuta `branch-plan`. Logs vía helper compartido.
- `.claude/skills/writing-handoff/SKILL.md` — skill de cierre de rama. Edita **exclusivamente** `HANDOFF.md` §1, §9, §6b y gotchas §7; **jamás** toca `MASTER_PLAN.md` / `ROADMAP.md` / `docs/**` (gobernados por docs-sync del PR, no por la skill). Persiste decisiones durables a memoria proyectil (type `project`). Logs vía helper compartido.
- `.claude/skills/_shared/log-invocation.sh` — helper POSIX bash que emite una línea JSONL por invocación a `.claude/logs/skills.jsonl` con shape mínimo y estable `{ts, skill, session_id, status}`. Sin `args`, sin `duration_ms`. Fallback `session_id: "unknown"` si `CLAUDE_SESSION_ID` ausente; `mkdir -p` del directorio. **Best-effort operacional**: si el modelo omite el último paso, se pierde traza de esa invocación pero el sistema nunca rompe; `stop-policy-check.py` trata ausencia de entry como "no invocación" → allow.
- `policy.yaml` — añade `skills_allowed: [project-kickoff, writing-handoff]` a top-level. **Esto es el flip-switch del D6 scaffold**: una vez declarado, toda invocación logged para la sesión actual que no esté en la lista deniega el Stop. Contrato tri-estado de `skills_allowed_list()` intacto (`None`/`SKILLS_ALLOWED_INVALID`/`()`/tupla poblada).
- `pytest.ini` (root-level) con `addopts = --import-mode=importlib`. Sin esto, `hooks/tests/` y `.claude/skills/tests/` colisionan como mismo package `tests` y el segundo falla `ModuleNotFoundError`.
- Tests: `.claude/skills/tests/test_skill_frontmatter.py` (24 casos parametrizados por slug — 4 clases: `TestStructure`, `TestFrontmatter`, `TestBody`, `TestSharedLogger`) + `hooks/tests/test_skills_log_contract.py` (11 casos — 3 clases: `TestLoggerShape`, `TestExtractorReadsLoggerOutput`, `TestEnforcementEndToEnd`). Este último es el test que cruza la integración con D6 usando los nombres reales (`project-kickoff`, `writing-handoff`), mientras `test_stop_policy_check.py` sigue usando placeholders `pos:*` como fixtures.
- `hooks/tests/test_lib_policy.py::test_real_skills_allowed_populated_by_e1a` — antes asertaba `is None`; renombrado y flippeado a `== ("project-kickoff", "writing-handoff")`. Lock-down del contrato entre `policy.yaml` y el accessor.

**Contrato fijado por la suite**:

- Skill primitive: `.claude/skills/<slug>/SKILL.md` + frontmatter YAML minimal. **No `skill.json`**. **No prefijo `pos:`** en `name`. **No campos inventados** más allá de `name` / `description` / `allowed-tools`.
- Description framed como `"Use when …"` — selección elegible por el modelo, **no trigger garantizado**.
- Log shape estable a 4 campos `{ts, skill, session_id, status}`. Extender requiere nueva rama + justificación + migración de `_extract_invoked_skills` + tests del contrato.
- `writing-handoff` NO toca `MASTER_PLAN.md` / `ROADMAP.md` / `docs/**`. Ampliar scope requiere rama E1c, no extensión silenciosa.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **C1 inline Bash call** (vs C2 hook nuevo / C3 sin log): logger se llama desde el body de la SKILL.md como último paso. Elegido por simplicidad y por no reabrir Fase D.
- **`writing-handoff` = Edit directo (scoped)** (vs diff-only): si la skill existe para escribir, que escriba; diff-only introduce fricción artificial. Condición aceptada: scope estricto §1/§9/§6b/gotchas.
- **`.claude/skills/_shared/`** (vs `_lib/`): utility compartida entre skills; evita confusión con `hooks/_lib/`.
- **Tests split**: frontmatter en `.claude/skills/tests/` (dominio skills), integración log↔stop-policy-check en `hooks/tests/` (dominio consumer).
- **`skills_allowed` poblado en esta rama** (vs diferirlo a E1b): `project-kickoff` es la primera skill que escribe `.claude/logs/skills.jsonl`; si hay skill + logger + hook scaffold, activar el scaffold en la misma rama cierra el loop.

**Resultado**: **610 passed + 1 skipped** en la suite conjunta `hooks/tests` + `.claude/skills/tests`. D6 regression intacta (575 baseline → 575 + 35 nuevos E1a). `stop-policy-check.py` entra en enforcement live con dos skills declaradas; fue `status: deferred` hasta este merge.

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § feat/e1a-skill-kickoff-handoff](ROADMAP.md), [MASTER_PLAN.md § Rama E1a](MASTER_PLAN.md), [.claude/rules/skills-map.md](.claude/rules/skills-map.md) y [docs/ARCHITECTURE.md § 5 Skills](docs/ARCHITECTURE.md).

## 15. Estado E1b (cerrada en rama, docs-sync en curso)

`feat/e1b-skill-branch-plan-interview` — **segunda rama de Fase E**. Completa el par de skills de orquestación Fase -1 que E1a dejó abierto: `branch-plan` (producer de los seis entregables) + `deep-interview` (clarificador socrático opt-in). Ambas heredan el contrato primitive-minimal canonizado en E1a sin reabrirlo.

**Entregables**:

- `.claude/skills/branch-plan/SKILL.md` — Fase -1 producer. Lee `MASTER_PLAN.md § Rama <slug>`, archivos de "Contexto a leer" por rangos, `HANDOFF.md §9`, git introspection cheap. Emite seis entregables en conversación (Resumen técnico / conceptual / Ambigüedades / Alternativas / Test plan / Docs plan). **Delega vía Agent tool inline** cuando el plan requiere leer ≥3 archivos no triviales: `subagent_type ∈ {Plan, code-architect, Explore}` según naturaleza; el subagent devuelve summary al tool result, la skill lo folds — no paste-through. **STOPS BEFORE marker** — no crea `.claude/branch-approvals/<slug>.approved`, no corre `git checkout -b`, no arranca Fase 1/2, no auto-invoca `deep-interview` (sólo sugiere opt-in en Ambigüedades). Logea via helper compartido.
- `.claude/skills/deep-interview/SKILL.md` — socratic clarifier. **Opt-in estricto**: tres condiciones deben valerse (invocación explícita + ambigüedad conceptual real + usuario disponible para dialog); cualquier miss → una línea + log `status: declined` + salida silenciosa. Lectura minimal-only (`MASTER_PLAN § Rama`, `HANDOFF §9`, `git log -10`). Pregunta en clusters de 1–3 preguntas, máximo 3–5 clusters, corta antes si resuelve. Cierra con **Clarified / Still open / Recommend** + **ratification gate** antes de escribir a memoria `type: project` — silencio ≠ consent. **Main-strict, sin subagent**: el coste está en el dialog, no en reading. **No muta docs, ROADMAP, MASTER_PLAN, HANDOFF ni `.claude/rules/`**. Logea via helper compartido (`status ∈ {declined, partial, ok}`).
- `policy.yaml` — `skills_allowed` extendido 2 → 4: `[project-kickoff, writing-handoff, branch-plan, deep-interview]`. Comentario inline actualizado ("E1a activated the scaffold, E1b extends to 4 skills"). `stop-policy-check.py` continúa en enforcement live, ahora con 4 skills aceptadas.
- Tests (extensión, no reescritura):
  - `.claude/skills/tests/test_skill_frontmatter.py` — constante `E1A_SKILLS` renombrada a `E1_SKILLS_KNOWN` (contract-bound al allowlist, no era-bound) + extendida a 4 entries. Todos los tests parametrizados (11 por skill × 4 skills = 44 automáticos) cubren el contrato sin cambio de código en los tests mismos. Añadidas dos clases `TestBranchPlanBehavior` (3 casos: fase_minus_one_deliverables + marker_disclaim + stop_signal) + `TestDeepInterviewBehavior` (3 casos: socratic + opt_in + no_silent_mutation).
  - `hooks/tests/test_lib_policy.py::test_real_skills_allowed_populated_by_e1a` renombrado a `_by_e1b`; tupla esperada crece a 4 entries.
  - `hooks/tests/test_skills_log_contract.py::TestEnforcementEndToEnd::test_all_four_e1_skills_end_to_end` — emite una línea JSONL por cada una de las 4 skills, invoca Stop hook, asserta allow. Guarda contra typo silencioso en policy / logger / Stop hook rompiendo el contrato 4-skills.

**Contrato fijado por la suite** (extiende E1a sin reabrirlo):

- Primitive frontmatter inmutable: `name` / `description` / `allowed-tools`; sin `skill.json`; sin prefijo `pos:`; sin campos inventados (`context`, `model`, `agent`, `effort`, `hooks`, `user-invocable`, `disable-model-invocation`). Description `"Use when ..."`. Logger best-effort step final.
- `branch-plan` **nunca** crea marker / abre rama / auto-invoca `deep-interview`. Tests `TestBranchPlanBehavior::marker_disclaim` + `::stop_signal` lock down el disclaim en el body. Delegation vía Agent tool inline es **primitive-correct**: el primitive no soporta `context: fork` como campo frontmatter, pero el subagent corre en fork real — la skill sólo recibe summary.
- `deep-interview` **es opt-in**. Tests `TestDeepInterviewBehavior::opt_in` lock downs the gating; `::no_silent_mutation` asegura ratification gate. Auto-trigger requiere rama E1c nueva con justificación — el framing actual es deliberado.
- `skills_allowed` = 4 entries enforce vivo. La ausencia del 5º/6º/... slot cuando se invoque una skill no listada seguirá produciendo deny exit 2 (contrato D6 intacto).

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Decisión A1.a `branch-plan` delegation** (vs A1.b main-strict): delegación inline vía Agent tool. Razón: Fase -1 arquitectónica puede requerir cross-file analysis no trivial; cargar todo en main contamina contexto. Delegación inline es el **fork-aproximado primitive-correct**. Ramas lightweight saltan la delegación y emiten los seis entregables directamente.
- **Decisión A1.c `deep-interview` main-strict** (vs A1.a con subagent): conversational, sin subagent. Razón: el coste NO está en reading (body dice literal "do NOT read `docs/ARCHITECTURE.md` top-to-bottom"); está en el dialog del usuario. Un subagent intermediaría sin valor.
- **Decisión A5.a — fix `skills.md` drift en E1b** (vs A5.b diferir a E1c): reconciliación en la misma rama que entrega las skills cuyo body es el testigo del contrato. Cambios al rule file: bloque `Frontmatter obligatorio` inflado eliminado + reemplazado por referencia al shape canónico en `skills-map.md` (fuente única); `Logging` reescrito con patrón `log-invocation.sh` + best-effort; corrección `/pos:kickoff` → `project-kickoff` y `/pos:handoff-write` → `writing-handoff` (eco de E1a que faltaba propagar); sección `Criterios context: fork` reescrita como nota histórica.
- **Framing ajustes explícitos** (aprobados en Fase -1): `branch-plan` lleva disclaim literal "no crea marker / no abre rama / no ejecuta Fase -1 auto / solo produce paquete para aprobación" en `Scope (strict)` + `Explicitly out of scope`. `deep-interview` lleva disclaim literal "opt-in real / no insiste / resume y se detiene / no muta docs/memoria salvo ratificación del usuario" en `Framing` + `Failure modes` + `Explicitly out of scope`.

**Resultado**: **639 passed + 1 skipped** en la suite conjunta `hooks/tests` + `.claude/skills/tests` (+29 vs baseline E1a de 610: 22 parametrizados por `E1_SKILLS_KNOWN` 2→4 + 3 branch-plan behavior + 3 deep-interview behavior + 1 log-contract integration). E1a regression intacta. `test_real_skills_allowed_populated_by_e1b` flippa el pinpoint anterior (tupla 2→4). `stop-policy-check.py` sigue en enforcement live sin cambio de código, sólo con allowlist ampliada.

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § feat/e1b-skill-branch-plan-interview](ROADMAP.md), [MASTER_PLAN.md § Rama E1b](MASTER_PLAN.md), [.claude/rules/skills-map.md](.claude/rules/skills-map.md) y [.claude/rules/skills.md](.claude/rules/skills.md) (reconciliado en esta rama).

## 16. Estado E2a (cerrada en rama, docs-sync en curso)

`feat/e2a-skill-review-simplify` — **tercera rama de Fase E**, primer par del bloque calidad. Cierra el ciclo pre-PR con dos skills orquestadas en orden canónico `simplify → pre-commit-review`: primero reduce el diff, luego el review opera sobre el diff ya ligero. Ambas heredan íntegro el contrato primitive-minimal de E1a/E1b y lo extienden con patrones nuevos (writer-scoped-al-diff + Agent-tool hybrid delegation).

**Entregables**:

- `.claude/skills/pre-commit-review/SKILL.md` — skill delegadora al subagent `code-reviewer` vía Agent tool inline. Scope hybrid: main prepara context ligero (branch kickoff + invariantes citados en `.claude/rules/*.md` aplicables al diff); el subagent recibe ese context + `git diff main...HEAD` completo + asks explícitos (bugs / logic / security / scope adherence / invariant violations), corre en fork real y devuelve summary confidence-filtered; el main folds (dedup + file:line + severity order + veredicto `clean to PR | findings blocking | findings advisory only`) — **no paste-through**. **Nunca edita, nunca abre PR, nunca sustituye a `simplify`**. Logea via helper compartido. Fallback declarado: si el runtime Agent tool no expone `code-reviewer`, fall back a `general-purpose` con task prompt equivalente.
- `.claude/skills/simplify/SKILL.md` — skill reductora writer-scoped. `allowed-tools` incluye `Edit` (diferencia clave con `pre-commit-review`). Scope derivado en step 1 via `git diff --name-only main...HEAD`; **todo `Edit` call valida que el `file_path` pertenezca a esa lista** — si no, reclassify as `skip (out of scope)`. **No crea archivos nuevos**, **no toca archivos fuera del diff**, **no cambia comportamiento**, **no busca bugs** (ese es `pre-commit-review`), **no hace refactor mayor**. Targets declarados: redundancia / ruido / complejidad accidental / abstracción prematura. Cierra con reporte dos partes: "qué simplificó / what was simplified" + "qué decidió no tocar / what it chose not to touch" con razón por cada skip.
- `policy.yaml.skills_allowed` extendida 4 → 6: `[project-kickoff, writing-handoff, branch-plan, deep-interview, pre-commit-review, simplify]`. Comentario inline actualizado (`E1a scaffold → E1b 4 skills → E2a 6 skills`). `stop-policy-check.py` sigue en enforcement live, ahora con 6 skills aceptadas — sin cambio de código en el hook.
- Tests (extensión, no reescritura):
  - `.claude/skills/tests/test_skill_frontmatter.py` — constante `E1_SKILLS_KNOWN` renombrada a `ALLOWED_SKILLS` (contract-bound al allowlist entero, no era-bound) + extendida 4 → 6. Todos los tests parametrizados (11 por skill × 6 skills = 66 automáticos) cubren el contrato sin cambio. Dos clases nuevas: `TestPreCommitReviewBehavior` (3 casos: delegation a `code-reviewer` + scope `git diff main...HEAD` + disclaim de escritura y de reemplazo de `simplify`) + `TestSimplifyBehavior` (4 casos: `allowed-tools` incluye `Edit` + scope derivado + reducer framing + forma del reporte final).
  - `hooks/tests/test_lib_policy.py::test_real_skills_allowed_populated_by_e1b` renombrado a `_by_e2a`; tupla esperada crece 4 → 6 entries.
  - `hooks/tests/test_skills_log_contract.py::test_all_four_e1_skills_end_to_end` renombrado a `test_all_six_e1_e2a_skills_end_to_end`; allowlist + loop cubren las 6 skills.

**Contrato fijado por la suite** (extiende E1a + E1b sin reabrirlos):

- Primitive frontmatter inmutable (`name` / `description` / `allowed-tools`); sin `skill.json`; sin prefijo `pos:`; sin campos inventados. Precedentes E1a + E1b intactos.
- `pre-commit-review` **nunca** reescribe código, **nunca** aplica fixes, **nunca** abre PR, **nunca** sustituye a `simplify`. Test `TestPreCommitReviewBehavior::test_body_disclaims_writing_and_replacement` lock downs los 4 tokens literales (`findings` + uno de `does not rewrite` / `does not apply` / equivalentes + `simplify` + uno de `does not replace` / `not a substitute`).
- `simplify` **nunca** crea archivos, **nunca** toca archivos fuera del diff, **nunca** cambia comportamiento, **nunca** busca bugs, **nunca** hace refactor mayor. Los 4 tests `TestSimplifyBehavior` lock down cada disclaim + la derivación determinista del scope + la forma del reporte final.
- `ALLOWED_SKILLS = 6` entries enforce vivo. Invocar una skill no listada sigue produciendo deny exit 2 (contrato D6 intacto).
- Canonical order `simplify → pre-commit-review` documentada en ambos bodies. Ambas disclaim replacement mutuo.

**Ajustes vs plan original (Fase -1 aprobada)**:

- **Decisión A1.b writer-scoped strict** (vs A1.a read-only + user aplica): `simplify` edita directo archivos del diff; scope derivado via `git diff --name-only main...HEAD`; disciplina declarada en body + locked via 4 behavior tests. Tradeoff consciente: el usuario no ve diff de simplify para pre-approval — se compensa con reporte final que hace explícito el criterio del LLM.
- **Decisión A2.c hybrid delegation** (vs A2.a all-main / A2.b all-subagent): main prepara context ligero + subagent analiza diff pesado + main folds summary. A2.a descartado por coste en contexto; A2.b descartado porque el subagent no vería invariantes repo-specific del `.claude/rules/`. Hybrid captura lo mejor. Precedente directo: `branch-plan` (E1b A1.a) delegation pattern.
- **Decisión A3.a rename atómico** (vs A3.b mantener `E1_SKILLS_KNOWN` + añadir `E2_SKILLS_KNOWN`): `ALLOWED_SKILLS` contract-bound al allowlist entero, no a la era. Rename trae update coordinado de `.claude/rules/skills.md` línea 61.
- **Decisión A5 hardcode subagent name + disclaimer** (vs helper runtime): una sola skill consumidora hoy; abstracción prematura rechazada por regla #7 CLAUDE.md. Disclaimer literal apunta a `.claude/rules/skills.md § Fork / delegación`; fallback a `general-purpose` declarado. Reabrir en E2b si `audit-plugin` aporta segunda repetición.
- **YAML parse gotcha** atrapado en GREEN: `simplify` frontmatter v1 contenía `"Writer scoped: edits files..."` → el `: ` activaba parser YAML como mapping-separator y rompía el frontmatter entero. Fix: em-dash `Writer-scoped — edits files...`. Lección para futuras skills: evitar `palabra: palabra` dentro de descriptions.

**Resultado**: **668 passed + 1 skipped** en la suite conjunta `hooks/tests` + `.claude/skills/tests` (+29 vs baseline E1b de 639: 22 parametrizados por `ALLOWED_SKILLS` 4→6 + 3 pre-commit-review behavior + 4 simplify behavior + 1 log-contract integration actualizado + 1 `_populated_by_e2a` renombrado. El skip es el D5 intencional `TestIntegrationDiffUnavailable` por subprocess-no-cover). E1a + E1b + D1..D6 regression intacta. `test_real_skills_allowed_populated_by_e2a` flippa el pinpoint anterior (tupla 4→6). `stop-policy-check.py` sigue en enforcement live sin cambio de código, sólo con allowlist ampliada.

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § feat/e2a-skill-review-simplify](ROADMAP.md), [MASTER_PLAN.md § Rama E2a](MASTER_PLAN.md), [.claude/rules/skills-map.md](.claude/rules/skills-map.md) y [.claude/rules/skills.md](.claude/rules/skills.md) (rename `E1_SKILLS_KNOWN` → `ALLOWED_SKILLS` + notas E2a).

## 17. Estado E3a (✅ merged PR #23)

`feat/e3a-skill-compound-pattern-audit` — primer par de Fase E3 (skills patterns). Cierra el ciclo post-merge con `compound` (extracción de patrones reutilizables) + `pattern-audit` (auditoría del registry contra drift). Ambas heredan primitive minimal de E1a/E1b/E2a/E2b.

**Entregables**:

- `.claude/skills/compound/SKILL.md` — writer-scoped strict. Lee diff post-merge (filtra paths según `policy.yaml.lifecycle.post_merge.skills_conditional`); delega análisis a Agent tool (`code-architect` con fallback `general-purpose`); escribe propuestas a `.claude/patterns/` con formato canónico `# Pattern: <name>` + secciones `## Context/Signal/Rule/Examples/Last observed`. **NO refactoring de código**, solo propuestas de patrones; **STOP boundary** explícito: usuario revisa + aprueba merge del archivo de patrón.
- `.claude/skills/pattern-audit/SKILL.md` — read-only advisory main-strict (sin delegation). Lee entradas en `.claude/patterns/`; busca signals declarados en codebase via Grep/Bash; detecta drift entre signal declarado y código actual / examples / rule. Emite reporte diagnóstico sin mutar archivos. **STOP**: usuario decide si actualizar el patrón o reinvocar `/pos:compound` post-cambios.
- `policy.yaml.skills_allowed` extendido 8 → 10 (`compound`, `pattern-audit`).
- Tests behavior: 6 compound + 5 pattern-audit; allowlist parametrizada cubre frontmatter contract.

**Decisiones ratificadas**: `compound` writer-scoped strict (A1) + `pattern-audit` main-strict (A2) + `compound` delega a `code-architect` con fallback (A3). Formato de patrón fijado para todas las skills futuras de pattern-extraction.

**Detalle**: ver [MASTER_PLAN.md § Rama E3a](MASTER_PLAN.md), [.claude/rules/skills-map.md](.claude/rules/skills-map.md).

## 18. Estado E3b (cerrada en rama, docs-sync en curso)

`feat/e3b-skill-test-scaffold-audit-coverage` — **tercera rama de Fase E3 y cierre de Fase E**. Tres skills de calidad de tests, todas main-strict, todas heredando primitive minimal sin reabrir el frontmatter. Después de E3b, todas las skills core del plugin `pos` están entregadas; siguiente rama F1 abre Fase F (audit + selftest + marketplace).

**Entregables**:

- `.claude/skills/test-scaffold/SKILL.md` — **writer-scoped strict** (tercera del repo, tras `writing-handoff` E1a y `simplify` E2a). Detecta convención de tests del repo (co-located vs `tests/`) sobre archivos existentes; si ≥80% claro → escribe **solo** el test pair file derivado del source que el usuario provee; si ambigua → STOP + propone opciones top-2/3. **No modifica source code**, **no ejecuta pytest/vitest**, **no modifica thresholds/config**. Allowed-tools incluye `Write` + `Glob`/`Grep`/`Read` + `Bash(find:*)`/`Bash(git grep:*)` + logger.
- `.claude/skills/test-audit/SKILL.md` — **read-only advisory main-strict** (precedente: `pattern-audit` E3a). Discovery via Glob (`**/*.test.ts`, `**/test_*.py`, etc.); analyze cada test file estáticamente: flaky risk (asserts en `for`/`if` blocks via Grep), orphan (imports a paths que no existen), trivial (`assert True/False/1/0/""/None`); **declara candidate signals** (no "detecta") con file:line + reasoning, capped a 10 findings, severity tier orphan ≥ flaky > trivial. Cierre con disclaim literal de no-exhaustividad. **No ejecuta pytest/vitest**, **no modifica archivos**. Allowed-tools sin `Write`.
- `.claude/skills/coverage-explain/SKILL.md` — **read-only advisory main-strict**. Lee reportes existentes (`coverage/lcov.json`, `.coverage`, `coverage.json`, `htmlcov/`, `.nyc_output/coverage.json`); **declara strategy de parsing** (no "parsea") + confidence-level disclaim; analiza gaps por archivo (red <50%, yellow 50–75%, green >75%); propone targets mínimos viables (advisory, no mandatorio). **No ejecuta `npm run test-coverage`/`pytest --cov`**, **no modifica `coverage.threshold`/`pyproject.toml`/`package.json`/tests**. Allowed-tools sin `Write`, sin `git grep` (no necesario para parsear reportes).
- `policy.yaml.skills_allowed` extendido 10 → 13 (`test-scaffold`, `test-audit`, `coverage-explain`). Comentario inline actualizado (`E3a 10 skills → E3b 13 skills`). `stop-policy-check.py` sigue en enforcement live, ahora con 13 skills aceptadas — sin cambio de código en el hook.
- Tests (extensión, no reescritura):
  - `.claude/skills/tests/test_e3b_behavior.py` — 15 casos behavior contract en 3 clases (`TestScaffoldBehavior` 5 + `TestAuditBehavior` 5 + `TestCoverageExplainBehavior` 5). Lock-down de los disclaim literales del body: writer-scoped + STOP boundary; advisory + declares + candidate signals + tipos (flaky/orphan/trivial) + no-execution + read-only; reads + report strategy + no-execution + no-threshold-mod + minimum targets framing.
  - `.claude/skills/tests/_allowed_skills.py` — `ALLOWED_SKILLS` extendida 10 → 13; header docstring con línea E3b.
  - `hooks/tests/test_lib_policy.py::test_real_skills_allowed_populated_by_e3b` (rename desde `_by_e3a`) — tupla esperada crece 10 → 13.
  - `hooks/tests/test_skills_log_contract.py::test_all_thirteen_e1_e3b_skills_end_to_end` (rename desde `_ten_e1_e3a_`) — emite una línea JSONL por cada una de las 13 skills via shared logger, invoca Stop, asserta allow.

**Contrato fijado por la suite** (extiende E1..E3a sin reabrirlos):

- Primitive frontmatter inmutable; sin `skill.json`; sin prefijo `pos:`; sin campos inventados. Precedentes E1a + E1b + E2a + E2b + E3a intactos.
- `test-scaffold` **nunca** modifica source, ejecuta tests, modifica config, ni crea archivo cuando convención ambigua (STOP + propose).
- `test-audit` **nunca** ejecuta pytest/vitest/jest, modifica archivos, ni garantiza exhaustividad. Wording locked: tests fallarían si el body usase "detects" sin `candidate`/`signal`/`declares`.
- `coverage-explain` **nunca** ejecuta `npm run test-coverage`/`pytest --cov`, modifica thresholds/config, ni mandata target (advisory, user decides).
- `ALLOWED_SKILLS = 13` entries enforce vivo. Invocar una skill no listada sigue produciendo deny exit 2 (contrato D6 intacto).

**Ajustes vs plan original (Fase -1 aprobada con dos iteraciones)**:

- **V1 → V2 recorte de scope**: la primera Fase -1 listaba `Bash(vitest:*)` y `Bash(pytest:*)` en allowed-tools de `test-audit`/`coverage-explain` y prometía "valid syntax/linting" como behavior test. Rechazado por el usuario: "hay que recortar scope para no prometer motores de análisis/generación que esta rama no implementa." V2: cero ejecución, allowed-tools subset estricto, behavior tests verifican framing literal — no capabilities.
- **Wording correction post-V2**: "declares candidate signals" (no "detects"); "reads and explains coverage report data" / "declares missing coverage strategy" (no "parses coverage reports"). Aplicado en `description` + body.
- **YAML parse gotcha** (precedente E2a `simplify`): descripciones de `test-audit` y `coverage-explain` contenían colons dentro de paréntesis (`"declares candidate signals: flaky..."`). El `: ` activaba parser YAML como mapping-separator y rompía el frontmatter entero. Fix inmediato en commit `f98764d`: quote toda la description con `"..."`. Lección reforzada de E2a — generalizable: cuando una description tenga `palabra: palabra` sin comillas, fallará silently el frontmatter.

**Resultado**: la suite conjunta `hooks/tests` + `.claude/skills/tests` añade los renames de 2 tests integration + 22 parametrizados via `ALLOWED_SKILLS` 10→13 + 15 behavior contract; sin regresión D1..D6 + E1a..E3a. CI verde tras docs-sync (`ROADMAP.md` E3 ✅, `HANDOFF.md` §1+§9+§17+§18 nuevos, `MASTER_PLAN.md § Rama E3b` expandida + cierre `✅ PR #24`, `.claude/rules/skills-map.md` filas E3b finalizadas).

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § feat/e3b-skill-test-scaffold-audit-coverage](ROADMAP.md), [MASTER_PLAN.md § Rama E3b](MASTER_PLAN.md), [.claude/rules/skills-map.md](.claude/rules/skills-map.md).

## 19. Estado F1 (cerrada en rama, docs-sync en curso)

`feat/f1-skill-audit-session` — **primera rama de Fase F**, abre el bloque audit + release tras cierre completo de Fase E. Una skill nueva, read-only advisory main-strict, hereda primitive minimal sin reabrir frontmatter. Cierra el ciclo determinismo declarado en `docs/ARCHITECTURE.md § Determinismo` capa 3 (la capa que faltaba poblar): comparar lo que `policy.yaml` declara contra lo que `.claude/logs/` realmente registra.

**Entregables**:

- `.claude/skills/audit-session/SKILL.md` — read-only advisory main-strict (precedente: `pattern-audit` E3a, `audit-plugin` E2b, `compress` E2b, `test-audit` + `coverage-explain` E3b). Compara **tres superficies explícitas** de `policy.yaml` contra `.claude/logs/`: (1) `skills_allowed` ↔ `skills.jsonl` invocations distintas con prefijo `pos:` normalizado; (2) `lifecycle.<gate>.hooks_required` ↔ archivos `<hook>.jsonl` (existencia + nonempty); (3) `audit.required_logs` ↔ existencia + nonempty + mtime. Reporte estructurado por surface (3 secciones + summary line con counts). **Pre-existing drift expected**: hoy `audit.required_logs` declara `hooks.jsonl` pero los hooks logean a per-hook files; la skill reporta esto como Bucket 3 candidate y **no auto-fixea** — el usuario decide. Que el finding emerja en la primera invocación es evidencia de que el advisor funciona.
- Allowed-tools: `Glob`, `Grep`, `Read`, `Bash(find:*)`, `Bash(wc:*)`, `Bash(.claude/skills/_shared/log-invocation.sh:*)`. **Sin `Bash(git log:*)`** (recortado por ajuste 2 del usuario en Fase -1; la skill no necesita git introspection — sólo filesystem + policy parse), **sin `Edit`/`Write`** (advisory contract), **sin Agent tool** (main-strict explícito).
- `policy.yaml.skills_allowed` extendido 13 → 14 (`audit-session`). Comentario inline actualizado (`E3b 13 skills → F1 14 skills`). `stop-policy-check.py` sigue en enforcement live, ahora con 14 skills aceptadas — sin cambio de código en el hook.
- Tests (extensión, no reescritura):
  - `.claude/skills/tests/test_skill_frontmatter.py` — añadida `TestAuditSessionBehavior` con 5 casos (3 surfaces declaration / advisory-only / main-strict no delegation / 30-day window declaration / prefix normalization assumption). Tokens locked: `skills_allowed`+`lifecycle`+`hooks_required`+`required_logs`; `advisory`/`read-only`/`does not modify`/`no modifica`; ausencia de `subagent`/`code-architect`/`agent(`; `30`+`day`/`review window`; `pos:`+`normaliz`.
  - `.claude/skills/tests/_allowed_skills.py` — `ALLOWED_SKILLS` 13 → 14; header docstring con línea F1.
  - `hooks/tests/test_lib_policy.py::test_real_skills_allowed_populated_by_e3b` rename a `_by_f1`; tupla 13 → 14.
  - `hooks/tests/test_skills_log_contract.py::test_all_thirteen_e1_e3b_skills_end_to_end` rename a `test_all_fourteen_e1_e3b_f1_skills_end_to_end`; allowlist + loop cubren las 14 skills.

**Contrato fijado por la suite** (extiende E1..E3b sin reabrirlos):

- Primitive frontmatter inmutable; sin `skill.json`; sin prefijo `pos:`; sin campos inventados. Precedentes E1a..E3b intactos.
- `audit-session` **es read-only advisory**: nunca modifica `policy.yaml`, nunca rota/trunca/edita logs, nunca auto-fixea drift detectado.
- `audit-session` **es main-strict**: ausencia de tokens `subagent` / `code-architect` / `agent(` enforce vivo. Si una rama futura propone delegation, abrir branch nueva con justificación (regla #7 CLAUDE.md: ≥2 repeticiones antes de abstraer).
- `30-day review window` declarado como **textual guidance** para el lector humano — la skill no ejecuta date arithmetic, no filtra entries por timestamp, no podría aunque quisiera (allowed-tools subset estricto). El test valida declaración del body, no comportamiento de date math (ajuste 3 del usuario en Fase -1).
- `pos:<slug>` ↔ `<slug>` normalization assumption explicit en body — `policy.yaml.skills_allowed` lista plain slugs y `policy.yaml.lifecycle.*.skills_required` lista user-facing forms (`pos:` prefix); reconciliar es decisión consciente, no un bug.
- `ALLOWED_SKILLS = 14` entries enforce vivo. Invocar una skill no listada sigue produciendo deny exit 2 (contrato D6 intacto).

**Ajustes vs plan original (Fase -1 aprobada con 3 ajustes obligatorios del usuario)**:

- **Ajuste 1 — verificar shape de `policy.yaml` antes del body**: confirmé `lifecycle.<gate>.hooks_required` y `audit.required_logs` como claves canónicas existentes. Sin verificación el body habría usado nombres aproximados.
- **Ajuste 2 — recortar `Bash(git log:*)` de allowed-tools**: la skill no necesita git introspection (sólo lee policy + filesystem de logs). Allowed-tools final: 6 entries.
- **Ajuste 3 — test del 30-day window valida declaración, no ejecución**: la primera versión podría haber asertado sobre filtrado real de entries por timestamp, empujando scope hacia date arithmetic. Reformulado para asertar sólo declaración en el body.
- **Decisiones A1.a..A6.a ratificadas en Fase -1**: A1.a 3 surfaces (no exhaustive auditor); A2.a 30-day window textual; A3.a prefix normalization explícito; A4.a `hooks.jsonl` pre-existing drift reportado, no auto-fixed; A5.a report estructurado por surface; A6.a `audit.session_audit.schedule` documental (cron / CI hook diferido).

**YAML parse gotcha evitado**: por precedente E2a `simplify` + E3b `test-audit/coverage-explain`, la description fue redactada sin `palabra: palabra` para evitar parse-as-mapping-separator. Confirmed via test suite verde en GREEN inicial.

**Resultado**: suite conjunta `hooks/tests` + `.claude/skills/tests` arroja **793 passed + 1 skipped** (sin regresión D1..D6 + E1a..E3b; +5 behavior + 22 parametrizados via `ALLOWED_SKILLS` 13→14 + 2 renames integration). El skip es el D5 intencional `TestIntegrationDiffUnavailable` por subprocess-no-cover. CI verde tras docs-sync (`ROADMAP.md` Fase F abierta + § F1 detallado, `HANDOFF.md` §1+§9+§19 nuevos, `MASTER_PLAN.md § Rama F1` expandida + cierre `✅ PR pendiente`, `.claude/rules/skills-map.md` fila `/pos:audit-session` populada).

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § feat/f1-skill-audit-session](ROADMAP.md), [MASTER_PLAN.md § Rama F1](MASTER_PLAN.md), [.claude/rules/skills-map.md](.claude/rules/skills-map.md).

## 20. Estado F2 (cerrada en rama, docs-sync en curso)

`feat/f2-agents-subagents` — **segunda rama de Fase F**. Cierra la asimetría heredada de E2a/E3a: hasta F1 las skills `pre-commit-review` y `compound` delegaban a `code-reviewer` / `code-architect` (defaults de Claude Code, no propiedad del plugin). F2 entrega los subagents como contratos del plugin con namespace `pos-*` y flippea las skills consumidoras al nuevo nombre, sin tocar el shape ni el flujo. Tras F2, el plugin tiene primitive-correct ownership de toda su superficie (skills + hooks + agents + policy).

**Entregables**:

- `agents/pos-code-reviewer.md` — plugin subagent para branch-diff review. Consumido por `pre-commit-review` (E2a). Frontmatter primitive-correct (`name` + `description` + `tools` comma-separated string + `model: sonnet`). Body declara las 5 capacidades: bugs / logic errors / security vulnerabilities / scope adherence / invariant violations. Output contract: findings agrupados por severidad (blocker/high/medium/nit), confidence-filtered, `file:line` refs. Hard limits: no `Edit`, no `Write`, no PR, no invocación de otras skills/subagents.
- `agents/pos-architect.md` — plugin subagent para pattern extraction + cross-file design. Consumido por `compound` (E3a). Frontmatter primitive-correct. Body declara 3 dimensiones: pattern extraction (≥2 repeticiones, regla #7 CLAUDE.md), architectural design (cohesión + tradeoffs), cross-file consistency. Output contract: patterns en formato canónico (Name/Context/Signal/Rule/Examples/Rationale) listo para que `compound` los folde en `.claude/patterns/<slug>.md`. Hard limits: no refactor, no `Edit`, no overwriting de patterns existentes.
- `.claude/skills/pre-commit-review/SKILL.md` — flip `code-reviewer` → `pos-code-reviewer` (description + body + steps + failure modes). Fallback a `general-purpose` se mantiene literal — protege contra runtimes que no expongan agents del plugin.
- `.claude/skills/compound/SKILL.md` — flip `code-architect` → `pos-architect` (mismo patrón). Fallback `general-purpose` intacto.
- `agents/tests/test_agent_frontmatter.py` (NEW) — 26 contract tests parametrizados por `ALLOWED_AGENTS = ["pos-code-reviewer", "pos-architect"]`: 4 clases (`TestStructure`, `TestFrontmatter`, `TestBody`, `TestCodeReviewerCapability` + `TestArchitectCapability`). `ALLOWED_FRONTMATTER_KEYS = REQUIRED_FRONTMATTER_KEYS = {name, description, tools, model}` (todos requeridos post-revisión PR); `VALID_MODELS = {sonnet, opus, haiku}`; `F2_REQUIRED_MODEL = "sonnet"`. Validan: file exists + parses; keys ⊆ allowed; todos los 4 keys requeridos; `name` == filename slug; namespace `pos-*`; `tools` comma-separated string (NO YAML list — diferencia con skill primitive — con validación de tokens no vacíos y sin whitespace en el nombre antes de `(...)`); `model` válido + `model == "sonnet"` lockeado por F2 Fase -1 (1); body >100 chars; capability surfaces (bug/security/scope/invariant para `pos-code-reviewer`; pattern/design/cross-file consistency para `pos-architect`).
- `.claude/skills/tests/test_skill_frontmatter.py` — `TestPreCommitReviewBehavior::test_delegates_to_pos_code_reviewer` + `TestCompoundBehavior::test_body_delegates_to_pos_architect_with_fallback` flippean a los nuevos nombres + asertan literalmente fallback `general-purpose`. `pattern-audit` + `audit-session` negation lists incluyen ahora `pos-architect` / `pos-code-reviewer` (forward-compat: main-strict skills nunca deben referenciar plugin subagents).

**Contrato fijado por la suite** (extiende E1..F1 sin reabrirlos):

- **Plugin agent primitive**: `agents/<slug>.md` + frontmatter `{name, description, tools, model}`. **Shape distinto al skill primitive** — `tools` es comma-separated string (oficial Claude Code subagent format), no YAML list `allowed-tools`. Sin campos inventados (precedente E1a `feedback_skill_primitive_minimal.md` aplicado a primitive paralelo).
- **Namespace `pos-*` obligatorio** para evitar colisión con built-in defaults de Claude Code (`code-reviewer`, `code-architect`, `Plan`, `Explore`, `general-purpose`) y con user/project agents externos. Test `test_name_uses_pos_namespace` lockea esto.
- **Fallback `general-purpose` explícito** en bodies de skills consumidoras — protege contra runtimes que no exponen agents del plugin (Claude Code antes de discovery del directorio `agents/`, entornos minimal, etc.).
- **`auditor` diferido**: no tiene consumer real hoy; entregarlo violaría regla #7 CLAUDE.md (≥2 repeticiones documentadas). Reabrir en rama dedicada (F2b o post-F4) si una skill futura lo requiere.
- **`policy.yaml.agents_allowed` diferido**: no hay enforcement consumer (Stop hook lee `skills.jsonl`, no `agents.jsonl`; no hay log de invocaciones de subagents). Documentado como deferred — reabrir cuando un hook futuro requiera enforcement.

**Decisiones cerradas en Fase -1 (ratificadas por el usuario)**:

- (1) **Shape primitive**: oficial Claude Code subagent format (`name` + `description` + `tools` comma-separated + `model: sonnet`); body Markdown como system prompt. Sin campos inventados.
- (2) **Scope**: 2 agents (no 3). `auditor` diferido por falta de consumer.
- (3) **Naming**: namespace `pos-*` (no override silencioso de built-ins, no nombres a secas).
- (4) **Policy**: `agents_allowed` no añadido en F2 (no enforcement consumer hoy). Sin tocar `policy.yaml`, `hooks/_lib/policy.py`, ni extender `audit-session`.
- (5) **Tests**: contract tests parametrizados por `ALLOWED_AGENTS` + behavior flips de skills consumidoras + forward-compat negation en main-strict skills (`pattern-audit` + `audit-session` no deben mencionar plugin subagents).
- (6) **Docs-sync**: ROADMAP fila F2 + sección F + nuevo bloque ✅; HANDOFF §1+§8+§9+§20; MASTER_PLAN § Rama F2 expandida; `.claude/rules/skills.md § Fork / delegación` actualiza precedentes a plugin agents; `.claude/rules/skills-map.md` añade sección "Subagents del plugin"; `docs/ARCHITECTURE.md § 6 Agents` reescrita post-revisión PR (nuevo top-level `agents/` es superficie arquitectónica del plugin aunque no esté enforced por el `pre-pr-gate` conditional).

**Ajustes vs plan original**:

- **Recorte v1 → v2 (decisión usuario)**: la primera Fase -1 listaba 3 agents (`code-reviewer`, `architect`, `auditor`) sin namespace + extensión de `policy.yaml.agents_allowed` + cambios en `hooks/_lib/policy.py`. El usuario rechazó: scope a 2 agents (regla #7 sobre `auditor`), namespace `pos-*` obligatorio, **no** tocar `policy.yaml` ni hooks (sin enforcement consumer hoy). El v2 aprobado es el que se implementó.
- **Hardcode literal con disclaimer** (precedente E2a A5): los bodies hardcodean `pos-code-reviewer` / `pos-architect` con fallback `general-purpose`. Una sola consumidora por agent hoy → no justifica helper runtime (regla #7). Reabrir si una segunda skill aporta repetición.

**Resultado**: **819 passed + 1 skipped** (vs baseline F1 de 793; +26 netos del nuevo `agents/tests/test_agent_frontmatter.py` parametrizado por 2 slugs × 13 métodos. Las behavior flips de `test_skill_frontmatter.py` actualizan assertions de tests existentes — no añaden count). Sin regresión D1..D6 / E1a..E3b / F1. `stop-policy-check.py` sigue en enforcement live con `ALLOWED_SKILLS = 14` (F2 no añade skills, solo agents). El skip es el D5 intencional `TestIntegrationDiffUnavailable` por subprocess-no-cover.

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § feat/f2-agents-subagents](ROADMAP.md), [MASTER_PLAN.md § Rama F2](MASTER_PLAN.md), [.claude/rules/skills-map.md § Subagents del plugin](.claude/rules/skills-map.md), [.claude/rules/skills.md § Fork / delegación](.claude/rules/skills.md).

## 21. Estado F3 (cerrada en rama, docs-sync en curso)

`feat/f3-selftest-end-to-end` — **tercera rama de Fase F**. Entrega el selftest end-to-end del propio plugin: cierra el círculo "lo que el plugin promete enforce-ar contra repos generados, lo prueba sobre uno generado al vuelo", sin Claude Code runtime y sin invocaciones reales de skills/agents (cobertura estática queda en sus tests dedicados).

**Entregables**:

- `bin/pos-selftest.sh` (9 líneas) — wrapper bash mínimo (`#!/usr/bin/env bash` + `set -euo pipefail` + delega a `python3 bin/_selftest.py`). Sin lógica; entrypoint estable.
- `bin/_selftest.py` (~344 líneas) — orquestador stdlib Python. Por escenario: tmpdir + `npx tsx generator/run.ts --profile cli-tool.yaml --out <tmpdir>` para generar proyecto sintético, sobre-escribe la sección mínima de `synthetic/policy.yaml` que el escenario necesita, monta el sintético como git repo (`git init -b main` + commit baseline), invoca el hook real (`hooks/<name>.py`) vía subprocess con payload JSON, asserta exit + tokens en stdout/stderr/files. Imprime `[ok] D{N} {name}` o `[fail] D{N} {name}: <diag>`.
- `bin/tests/test_selftest_smoke.py` — 4 tests pytest sobre el contrato del wrapper.
- `bin/tests/test_selftest_scenarios.py` — 5 tests pytest, fixture `module-scoped` que corre `pos-selftest.sh` una vez y comparte stdout. Cada test asserta `"[ok] D{N} {name}"`.
- `.github/workflows/ci.yml` — nuevo job `selftest` (ubuntu × Python 3.11, sin matriz extendida — gates funcionales platform-agnostic, generación sintética es la op más cara). Setup Node + Python + `npm ci` + `pip install -r requirements-dev.txt`. Comando único: `pytest bin/tests -q`.
- `.claude/rules/ci-cd.md` — bullet "integración end-to-end" promovido de "Diferidos" a "Aterrizado". H3 `### Job selftest (entregado en F3)` documenta scope + qué corre + qué queda fuera + drift sintético ↔ meta-repo.

**Escenarios cubiertos** (5 funcionales-críticos):

- D1 pre-branch-gate: deny `git checkout -b` sin marker → allow tras `touch <marker>`.
- D3 pre-write-guard: deny `Write hooks/foo.py` sin test pair → allow tras crear `hooks/tests/test_foo.py`.
- D4 pre-pr-gate: deny `gh pr create` sin docs-sync (ROADMAP + HANDOFF) → allow tras commit que añade los docs.
- D5 post-action: tras `git merge` confirmado por reflog cuyo diff matchea trigger globs, hook emite advisory `Consider running /pos:compound`.
- D6 stop-policy-check: Stop con `session_id` rogue (allowlist + `skills.jsonl` con entry no permitida) deniega; `session_id` clean permite.

**Out of scope** (ratificado en F3 Fase -1):

- D2 session-start (informative, exit 0 sin enforcement) y D6 pre-compact (informative). Sin contrato deny/allow; cobertura via tests unitarios en `hooks/tests/`.
- Claude Code runtime: no instancia Claude Code, no invoca `pre-commit-review` / `compound` / `audit-session`, no dispatcha `/pos:compound`. Skills/agents se verifican estáticamente.
- D5b loader: cubierto **indirectamente** — los hooks D3/D4/D5 lo consumen y los escenarios sobre-escriben la sección relevante de `synthetic/policy.yaml`. Esto desacopla la cobertura de la migración del template `templates/policy.yaml.hbs` al shape post-D5b (drift abierto, reabrir en rama propia post-F3).

**Decisiones Fase -1 ratificadas**: A1.b (wrapper bash + orquestador Python + smoke pytest); A2 (subset funcional-crítico D1/D3/D4/D5/D6); A3 (tmpdir + cli-tool profile + generator real, no fixture); A4 (exit code + tokens, no golden diff); A5 (job `selftest` en `ci.yml`, no workflow separado, single matrix); A6 (no Claude runtime, no skills/agents reales).

**Ajustes durante implementación**:

- D5 trigger globs: `fnmatch` no recursa en `**/`. Corregido `generator/**/*.ts` → `generator/*.ts` (toplevel-only); `**/*.md` → `*.md`. Lección: si una rama futura necesita recursión real, switch a `pathlib.PurePath.match` o glob walker.
- D4 accessor doble-clave: `docs_sync_rules()` requiere **ambas** `docs_sync_required` AND `docs_sync_conditional` o devuelve `None`. Corregido añadiendo `docs_sync_conditional: []` al override.
- ci-cd.md placement de H3: la primera versión rompió la lista ordenada (MD029/MD032). Movido a después del item 3 (`release.yml`), antes de `## Workflows generados`.

**Resultado**: **829 passed + 1 skipped** (vs baseline F2 819 + 1 skip = +10 nuevos: 4 smoke + 5 D-scenarios + 1 GREEN smoke ya merged). Sin regresión D1..D6 + E1a..E3b + F1 + F2. Selftest end-to-end local ~1.2s.

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § feat/f3-selftest-end-to-end](ROADMAP.md), [MASTER_PLAN.md § Rama F3](MASTER_PLAN.md), [.claude/rules/ci-cd.md § Job selftest (entregado en F3)](.claude/rules/ci-cd.md), [docs/ARCHITECTURE.md § 10 Selftest end-to-end](docs/ARCHITECTURE.md).

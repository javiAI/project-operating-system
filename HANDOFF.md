# HANDOFF — quickref 30s

> Leer al arrancar sesión. Diseñado para llegar a "puedo ejecutar Fase -1 de la siguiente rama" en <1 minuto.

## 1. Snapshot

- Repo: `project-operating-system` (plugin `pos`).
- Fase actual: **D6 ✅ cerrada en rama** (`feat/d6-hook-pre-compact-stop`, PR pendiente — docs-sync + simplify en curso). Anterior: **D5b ✅ PR #17** (`8dc419a`). Siguiente tras merge D6: **E1a — `feat/e1a-skill-kickoff-handoff`** (arranque de Fase E, skills).
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

Hasta que `pos` tenga sus propias skills:

- `Explore` (>3 queries de búsqueda cross-archivo).
- `code-reviewer`, `code-architect`, `Plan` — subagents built-in.
- Skills globales del usuario (si las tiene en `~/.claude/skills/`).

## 9. Próxima rama

**E1a — `feat/e1a-skill-kickoff-handoff`** (tras merge de D6 — arranca Fase E, skills del plugin `pos`).

Scope (ver [MASTER_PLAN.md § Rama E1a](MASTER_PLAN.md)):

- Primera entrega de skills `/pos:*` reales. Dos skills core del ciclo de sesión: `/pos:kickoff` (snapshot 30s + detección de siguiente rama al arrancar sesión, `context: main`, sonnet) y `/pos:handoff-write` (persiste estado actual en `HANDOFF.md` + memoria antes de `/clear` o `/compact`, `context: main`, sonnet). Cierra la asimetría actual (hooks D vivos pero skills referenciadas en `skills-map.md` inexistentes — invocaciones fallan silenciosas).
- **Activación del scaffold Stop**: al aparecer la primera skill real, `skills_allowed` en `policy.yaml` pasa de ausente (`status: deferred` hoy) a poblada — `stop-policy-check.py` entra en enforcement live sin cambio de shape. E1a es el primer consumidor real del loop blocker-scaffold entregado en D6.
- **Log canónico `skills.jsonl`**: E1a emite la primera entrada de este archivo (hasta hoy inexistente) — formato `{timestamp, skill, status, ...}` leído por `stop-policy-check._extract_invoked_skills`. Shape exacto se cierra en Fase -1 de E1a.

Lectura mínima al arrancar:

- [MASTER_PLAN.md § Rama E1a](MASTER_PLAN.md) — scope + decisiones previas + contexto a leer.
- [.claude/rules/skills-map.md](.claude/rules/skills-map.md) — contrato completo de skills: lifecycle, modelo, context (main/fork), qué hace cada una. E1a entrega las 2 primeras filas del bloque "Core".
- [docs/ARCHITECTURE.md § 7 Determinismo](docs/ARCHITECTURE.md) — cómo skills + hooks encajan en las 3 capas; E1a empieza a llenar la Capa 2 (skills) que hasta hoy sólo tiene hooks.
- [policy.yaml](policy.yaml) — secciones `skills_allowed` (ausente hoy — primera redacción en E1a) y `lifecycle.skills_required` (advisory deferred en `pre-pr-gate`).
- [hooks/stop-policy-check.py](hooks/stop-policy-check.py) + [hooks/_lib/policy.py](hooks/_lib/policy.py) `skills_allowed_list()` — contrato que pasa a enforcement live cuando E1a declare allowlist.
- `.claude/skills/` + `.claude/agents/` — directorios **inexistentes hoy** en el meta-repo (sólo existen en `templates/.claude/` para el proyecto generado). E1a los crea por primera vez en el meta-repo y define su shape canónico.

**Notas de arranque Fase E** (primer cambio de dominio hooks → skills):

- Las skills `/pos:*` no tienen equivalente en la API de Claude Code idéntico a hooks — viven como prompts con frontmatter YAML en `.claude/skills/<name>.md`. Fase -1 E1a debe resolver: shape exacto de frontmatter, mecanismo de dispatch, cómo interactúa con `context: fork` (subagent).
- Los hooks **no cambian** en E1a — D6 cerró Fase D. E1a sólo crea skills; hooks quedan intactos.
- `stop-policy-check.py` pasa a enforcement live por simple populación de `skills_allowed` — no requiere nuevo código en el hook. Validar que el hook se dispara correctamente con una skill real invocada.

## 10. Estado D5 (cerrada en rama)

`post-action` vivo: en cada `PostToolUse(Bash)` aplica detección jerárquica 2 tiers. Tier 1 (`shlex.split`): matcher A `git merge <ref>` excluyendo flags de control `--abort/--quit/--continue/--skip`; matcher C `git pull` excluyendo `--rebase`/`-r`. Tier 2 (`git reflog HEAD -1 --format=%gs`): confirma `"merge "` (A) o `"pull:" | "pull "` sin `"pull --rebase"` (C) — evita disparar en `git merge --abort` o en pulls rebase-sin-flag. `gh pr merge` (matcher B) descartado en Fase -1 por ausencia de `tool_response.exit_code` garantizado en PostToolUse(Bash). Con ambos tiers confirmados: `git diff --name-only HEAD@{1} HEAD` + `fnmatch` contra `TRIGGER_GLOBS` / `SKIP_IF_ONLY_GLOBS` / `MIN_FILES_CHANGED=2` (mirror literal de `policy.yaml.lifecycle.post_merge.skills_conditional[0]`). Match → emite `additionalContext` sugiriendo `/pos:compound` (4 líneas, cap 3 paths + `(+N more)`); nunca dispatcha la skill (D5 advisory-only, E3a entrega la skill real). Exit 0 siempre — PostToolUse non-blocking (ni `permissionDecision` ni exit 2 bajo ningún camino). Double log: `post-action.jsonl` con 4 status (`tier2_unconfirmed`, `diff_unavailable`, `confirmed_no_triggers`, `confirmed_triggers_matched`) + `phase-gates.jsonl` evento `post_merge` sólo en los dos status confirmed — los advisory tier2/diff no cruzan la puerta del lifecycle. Pass-through (Tier 1 miss) silencioso (cero log, replica D1). 111 tests D5 (110 passed + 1 skip intencional — delegación interna entre integración y unit), 432 totales en `hooks/**`, 97% coverage sobre `post-action.py`; D1/D2/D3/D4 intactos. Hardcode de `policy.yaml` es la **segunda repetición tras D4** — regla #7 CLAUDE.md cumplida dos veces, precondición abierta para la rama policy-loader.

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § feat/d5](ROADMAP.md), [MASTER_PLAN.md § Rama D5](MASTER_PLAN.md) y [.claude/rules/hooks.md § Quinto hook](.claude/rules/hooks.md).

## 11. Estado D5b (cerrada en rama, docs-sync en curso)

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

## 12. Estado D6 (cerrada en rama, docs-sync en curso)

`feat/d6-hook-pre-compact-stop` — sexto y séptimo hook Python, cierre de Fase D antes de arrancar Fase E (skills). Dos entregas en un PR deliberadamente (decisión Fase -1 "both-together"): ambos hooks comparten el mismo nuevo accessor pattern sobre el loader D5b (`pre_compact_rules` + `skills_allowed_list`) y se testean contra el mismo fixture set — separarlos habría generado churn sin beneficio.

**`hooks/pre-compact.py` — PreCompact informative (shape D2, no-enforcement)**: lee `pre_compact_rules(cwd).persist` y emite una checklist en `additionalContext` antes de que Claude Code haga `/compact`. Exit 0 siempre; nunca `permissionDecision`. Happy path: header + bullet list de items a persistir (patrones, decisiones, marker files). Failure mode canónico (c.2): policy ausente o `lifecycle.pre_compact` ausente → `build_context` informativo minimal + log `status: policy_unavailable`. Safe-fail informative ante stdin corrupto: contexto degradado que señala el error + log `status: payload_error` — el hook nunca rompe el compact, sólo degrada su contexto. El wording exacto del `additionalContext` **no es contrato** (no lo citamos aquí): consultar `hooks/pre-compact.py` + `hooks/tests/test_pre_compact.py` si algún consumidor necesita inspeccionarlo. Double log: `pre-compact.jsonl` siempre; `phase-gates.jsonl` evento `pre_compact` **solo** en happy path (policy_unavailable y payload_error no cruzan la puerta del lifecycle).

**`hooks/stop-policy-check.py` — Stop blocker scaffold (shape D1, NO enforcement en producción hoy)**: este es el punto de framing más importante de D6. Hoy el hook está **activable pero desactivado**: `policy.yaml` no declara `skills_allowed`, así que `skills_allowed_list(cwd)` devuelve `None` y el hook entra en camino `status: deferred` — exit 0, pass-through silencioso. Cuando E1a declare una skill real y pueble `skills_allowed`, el hook **ya está listo sin cambio de código**: lee `.claude/logs/skills.jsonl` filtrando por el `session_id` del payload Stop actual via `_extract_invoked_skills`, compara contra la allowlist, y emite `permissionDecision: deny` + exit 2 si hay violación. Shape D1 canónico: safe-fail `_deny_payload` ante stdin malformado o `session_id` ausente/no-string (deny canónico, nunca allow blind — sin session_id no puede scopiarse enforcement). Contrato tri-estado de `skills_allowed_list`: `None` = sección ausente → `status: deferred`; `SKILLS_ALLOWED_INVALID` (sentinel) = presente pero mal formada → `status: policy_misconfigured` **observable** (NO colapsa con deferred — un typo en la policy no apaga enforcement silenciosamente); `()` = declarada vacía → deny-all explícito; tupla poblada = enforcement live. Session scoping: entradas de `skills.jsonl` con `session_id` distinto o ausente se ignoran (el log es append-only y acumula entre sesiones). Double log: solo en decisiones reales (deferred + policy_misconfigured + policy_unavailable van al hook log, no cruzan `phase-gates.jsonl`).

**Decisión anti-sobrerrepresentación (Fase -1)**: D6 entrega el shape + suite de tests + contrato, no enforcement. Documentación en MASTER_PLAN § Rama D6, `.claude/rules/hooks.md § Séptimo hook entregado`, y `docs/ARCHITECTURE.md § 7 (cuarta aplicación blocker — scaffold)` lo explicita: el hook "protege" en el sentido de que valida su propio shape y está listo; no en el sentido de que hoy impida ninguna skill (ninguna existe todavía).

**Consumo del loader**: dos accessors nuevos en `hooks/_lib/policy.py` (D5b + D6 = 5 accessors totales): `pre_compact_rules(repo_root) -> PreCompactRules | None` (nuevo dataclass `PreCompactRules(persist: tuple[str, ...])`) + `skills_allowed_list(repo_root) -> tuple[str, ...] | None | SkillsAllowedInvalid` (tri-estado explícito tras revisión PR — sentinel `SKILLS_ALLOWED_INVALID` separa "ausente" de "mal formada"). Ambos delegan a helpers internos del loader. Regla #7 CLAUDE.md respetada: dos consumidores nuevos, no un helper compartido prematuro.

**Resultado**: 575 tests verdes + 1 skip intencional (vs. 462+1 baseline D5b; +113 tests nuevos en D6 — 80 específicos de los dos hooks nuevos, 20 sobre loader extendido, 13 cobertura cruzada/session-scoping/misconfigured); `pre-compact.py` 89% coverage, `stop-policy-check.py` 89% coverage, `_lib/policy.py` extendido mantiene 97%. Hook suite completa sin regresión sobre D1..D5.

**Detalle + deferrals + ajustes**: ver [ROADMAP.md § feat/d6-hook-pre-compact-stop](ROADMAP.md), [MASTER_PLAN.md § Rama D6](MASTER_PLAN.md), [.claude/rules/hooks.md § Sexto hook + Séptimo hook](.claude/rules/hooks.md) y [docs/ARCHITECTURE.md § 7](docs/ARCHITECTURE.md).

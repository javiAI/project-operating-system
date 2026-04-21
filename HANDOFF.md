# HANDOFF — quickref 30s

> Leer al arrancar sesión. Diseñado para llegar a "puedo ejecutar Fase -1 de la siguiente rama" en <1 minuto.

## 1. Snapshot

- Repo: `project-operating-system` (plugin `pos`).
- Fase actual: **D3 ✅ cerrada en rama** (`feat/d3-hook-pre-write-guard`, PR pendiente de abrir). Anterior: **D2 ✅ PR #12** (`1346178`). Siguiente: **D4 — `feat/d4-hook-pre-pr-gate`**.
- Fuente de verdad ejecutable: [MASTER_PLAN.md](MASTER_PLAN.md).
- Estado vivo: [ROADMAP.md](ROADMAP.md).
- Arquitectura canonical: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

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
- El hook `pre-write-guard.py` **ya está vivo** desde D3: PreToolUse(Write) blocker. Bloquea con exit 2 la creación de archivos en paths enforced (`hooks/*.py` top-level + `generator/**/*.ts` excluyendo tests/fixtures) sin test pair co-located. Pass-through silencioso en edits sobre archivos existentes, en `hooks/_lib/**`, en tests/docs/templates/meta, y en paths fuera del repo. Bypass legítimo: crear primero `hooks/tests/test_<x>.py` o `<path>.test.ts` con un test que falle (RED), luego escribir la implementación.
- Otros hooks referenciados en `.claude/settings.json` (`post-action.py`, `pre-compact.py`, `stop-policy-check.py`) siguen ausentes — tolerados por Claude Code como no-op. Entregados en D4..D6.
- `policy.yaml` declarado pero no enforced todavía (Fase D4). Hasta entonces, docs-sync requiere disciplina manual.
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

**D4 — `feat/d4-hook-pre-pr-gate`**

Scope (ver [MASTER_PLAN.md § Rama D4](MASTER_PLAN.md)):

- Cuarto hook Python: `hooks/pre-pr-gate.py` — valida `policy.yaml` contra logs reales antes de abrir PR. Chequeos incluidos en el scope textual del plan: docs-sync (`ROADMAP.md` + `HANDOFF.md` + condicionales según `lifecycle.pre_pr.docs_sync_conditional`), skills required (qué skills deberían haber corrido según el lifecycle), CI dry-run, invariants. Shape blocker (PreToolUse(Bash) matcher `gh pr create` / `git push`).

Lectura mínima al arrancar:

- [MASTER_PLAN.md § Rama D4](MASTER_PLAN.md)
- [policy.yaml](policy.yaml) — esquema ya declarado en Fase A; D4 es el primer enforzador real.
- [.claude/rules/hooks.md](.claude/rules/hooks.md) (ya con "Tercer hook entregado" D3 + buckets de exclusión separados)
- [docs/ARCHITECTURE.md § 7 Determinismo](docs/ARCHITECTURE.md) (Capa 1 con pre-branch-gate + session-start + pre-write-guard como canónicos)
- [hooks/pre-branch-gate.py](hooks/pre-branch-gate.py) + [hooks/pre-write-guard.py](hooks/pre-write-guard.py) como patrones de referencia blocker (2 aplicaciones; reglas específicas distintas pero shape idéntico).
- [hooks/_lib/](hooks/_lib/) — `append_jsonl` + `now_iso` disponibles. Añadir al `_lib/` sólo si ≥2 hooks consumen el nuevo helper (regla #7).
- [.claude/logs/phase-gates.jsonl](.claude/logs/) — D4 lee este archivo para validar policy-vs-logs; eventos ya presentes: `branch_creation` (D1), `session_start` (D2), `pre_write` (D3). D4 añadirá `pre_pr` (o equivalente).

## 10. Estado D3 (cerrada en rama)

`pre-write-guard` vivo: en cada `PreToolUse(Write)` evalúa `tool_input.file_path`, lo normaliza contra `Path.cwd()`, y aplica el clasificador de 2 buckets de exclusión (tests/docs/templates/meta + `hooks/_lib/**`). Contrato crystal-clear:

- enforced + archivo inexistente + sin test pair → deny exit 2 con `decisionReason` que lista la ruta exacta esperada + comando `touch` + referencia a CLAUDE.md regla #3 + el write bloqueado.
- enforced + archivo inexistente + con test pair → allow exit 0 (log en ambos archivos).
- enforced + archivo ya existente → allow exit 0 — edit flow explícito (log en ambos archivos; D4 `pre-pr-gate` detecta la pérdida de cobertura sobre impl existente).
- excluido o fuera de scope → pass-through silencioso (cero stdout, cero log).

Enforced paths (hardcoded hasta D4): `hooks/*.py` top-level (excluye `_lib/` y `tests/`) + `generator/**/*.ts` (excluye `*.test.ts`, `__tests__/`, `__fixtures__/`). `generator/run.ts` queda enforced por decisión explícita Fase -1. Safe-fail blocker canonical (D1): stdin vacío / JSON inválido / top-level no-dict / `tool_input` no-dict → deny exit 2. `file_path` ausente o no-string → pass-through exit 0 (decisión Fase -1: no es malformación total). Double log: `.claude/logs/pre-write-guard.jsonl` + `.claude/logs/phase-gates.jsonl` (evento canónico `pre_write`). 84 tests D3 nuevos, 222 totales en `hooks/**` (D1 60 + D2 66 + D3 84 + lib indirectos), 96% coverage sobre `pre-write-guard.py`; D1/D2 intactos.

**Lo que D3 NO hace** (explícito):

- No modifica `.claude/settings.json` (ya referenciaba `./hooks/pre-write-guard.py` desde Fase A con `timeout: 3`; el hook sólo materializa el binario).
- No inyecta patterns path-scoped ni bloquea anti-patterns declarados (scope recortado en Fase -1; diferido a rama post-E3a cuando `/pos:compound` haya poblado `.claude/patterns/` y `.claude/anti-patterns/`).
- No valida docs-sync, coverage, CI dry-run ni policy.yaml (esa es la frontera con D4).
- No detecta merge ni dispara `/pos:compound` (D5).
- No mueve la lista de paths enforced a `policy.yaml` (decisión Fase -1: hardcode aceptado hasta que D4 tenga `policy.yaml` enforced).
- No introduce `read_jsonl` ni nuevos helpers en `_lib/` (sólo consume `append_jsonl` + `now_iso`; `sanitize_slug` no aplica aquí).
- No añade waiver `// test-waiver: <razón>` pese a estar mencionado en `.claude/rules/tests.md`. Ningún caso real lo demanda hoy (regla #7 — ≥2 repeticiones antes de abstraer).

Apuntes para quien arranque D4 (o cualquier rama post-D3):

- **Patrón hook consolidado (3ª aplicación)**: blocker (D1 + D3) vs informative (D2). D4 será la 3ª aplicación blocker; shape idéntico a D1/D3 (`hookSpecificOutput.permissionDecision: deny` + exit 2 en rutas de bloqueo; pass-through silencioso en el resto; safe-fail canonical sobre payload malformado).
- **`hooks/_lib/` estable** — `sanitize_slug` (D1, D4 probablemente no lo use), `append_jsonl`, `now_iso`. D4 puede necesitar un helper nuevo (p.ej. reader de `phase-gates.jsonl` para validar policy-vs-logs); añadir a `_lib/` sólo si ≥2 hooks lo consumen (regla #7).
- **`policy.yaml` entra en juego**: D4 es el primer hook que lo lee realmente. `docs/SAFETY_POLICY.md` + `docs/TOKEN_BUDGET.md` quedan fuera de scope D4 (se enforza policy.yaml, no las otras policy docs).
- **Evento canónico en phase-gates**: D4 añade `pre_pr` (o equivalente) al vocabulario ya instalado (`branch_creation` / `session_start` / `pre_write`).
- Carry-over Fase N+7: **sin carry-over abierto** al arrancar D4. Carry-over de C5 (copia real hooks/skills + `FileWrite.mode`) sigue abierto para rama post-E1a — no relevante para D4.
- Snapshots del generador (total 54) inalterados en D3 (no se tocó `generator/**`).

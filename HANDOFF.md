# HANDOFF — quickref 30s

> Leer al arrancar sesión. Diseñado para llegar a "puedo ejecutar Fase -1 de la siguiente rama" en <1 minuto.

## 1. Snapshot

- Repo: `project-operating-system` (plugin `pos`).
- Fase actual: **C5 ✅ cerrada en rama** (`feat/c5-renderers-skills-hooks-copy`, PR pendiente de abrir). Anterior: **C4 ✅ PR #8** (`c57570b`). Siguiente: **D1 — `feat/d1-hook-pre-branch-gate`**.
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

- El hook `pre-branch-gate.py` **aún no existe** (Fase D1). Hasta entonces, el marker es convención, no enforcement. Respetar manualmente.
- `policy.yaml` declarado pero no enforced todavía (Fase D4). Hasta entonces, docs-sync requiere disciplina manual.
- `/pos:*` skills no existen aún (Fase E*). Invocaciones fallarán silenciosas. Usar comportamiento manual equivalente.
- Todo hook declarado en `settings.local.json` con `_note: "Entregado en Fase D"` es un stub — el sistema tolera su ausencia.

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

**D1 — `feat/d1-hook-pre-branch-gate`**

Scope (ver [MASTER_PLAN.md § Rama D1](MASTER_PLAN.md)):

- Primer hook Python del plugin: `PreToolUse(Bash)` bloquea `git checkout -b <slug>` cuando `.claude/branch-approvals/<slug>.approved` no existe. Cierra la regla no-negociable #1 de CLAUDE.md pasando de convención manual a enforcement real.
- Abre la fase de hooks (`hooks/**`). Convenciones de test pair obligatorio (`hooks/tests/test_<x>.py`) vigentes desde este momento vía `.claude/rules/tests.md`.

Lectura mínima al arrancar:

- [MASTER_PLAN.md § Rama D1](MASTER_PLAN.md)
- [docs/ARCHITECTURE.md § 4 Hooks](docs/ARCHITECTURE.md)
- [.claude/rules/tests.md](.claude/rules/tests.md) (test pair + waiver)
- `.claude/settings.local.json` (estructura declarativa de hooks en Claude Code)

## 10. Estado C5 (cerrada en rama)

`.claude/` esqueleto emitido por `pos` en el proyecto generado: `.claude/settings.json` (`hooks: {}` + `_note` deferral, **sin** `permissions` baseline) + `.claude/hooks/README.md` (deferral a Fase D + nota sobre `FileWrite.mode`) + `.claude/skills/README.md` (deferral a Fase E). 18 archivos por profile cuando `workflow.branch_protection == true` (17 si `false`): 15 de C1–C4 + 3 de C5. Pipeline `allRenderers` compone `coreDocRenderers + policyAndRulesRenderers + testsHarnessRenderers + cicdRenderers + skillsHooksRenderers` desde `generator/renderers/index.ts`. Detalle en [ROADMAP.md § Progreso Fase C](ROADMAP.md).

**Lo que C5 NO hace** (explícito):

- No copia los hooks ejecutables del plugin al proyecto generado. La copia real de `hooks/**` queda diferida a rama post-D1 cuando el catálogo de hooks exista.
- No copia skills del plugin. La copia real de `.claude/skills/pos/**` queda diferida a rama post-E1a cuando el catálogo de skills esté auditado.
- No extiende el shape `FileWrite` con `mode`. Mientras `pos` no copie ejecutables reales, el shape `{ path, content }` basta. La extensión llegará en la primera rama que necesite preservar bit `+x`.

Apuntes para quien arranque D1 (o cualquier rama post-C):

- Patrón `renderer-group` consolidado (5ª aplicación: core + policy/rules + tests-harness + ci-cd + skills-hooks-skeleton). Cualquier grupo nuevo en fases posteriores sigue el mismo shape: frozen tuple + composición en `allRenderers`. `run.ts` no se toca.
- **Carry-over abierto — copia real hooks/skills + `FileWrite.mode`**: rama post-D1/E1a. Al abrir, añadir `mode?` al tipo `FileWrite`, extender `writeFiles` para respetarlo, reemplazar los 2 READMEs de C5 por contenido real copiado, y poblar `settings.json.hooks` con los hooks reales. Ver detalle en [.claude/rules/generator.md § Deferrals](.claude/rules/generator.md).
- `settings.json` **no** siembra `permissions` baseline en C5. Cuando D1+ introduzca hooks reales con superficie de permisos conocida, decidir si se materializa un `permissions` mínimo en el renderer o se delega al hook mismo al instalarse.
- CI hosts no-github (`gitlab`, `bitbucket`) siguen diferidos. Fase D/E no los reabren salvo señal explícita.
- `release.yml` / `audit.yml` / matrix multi-OS y multi-runtime siguen diferidos. Ramas propias futuras.
- `buildProfile` sigue sin materializar defaults: `valid-partial` declara 4 paths explícitos hoy (`testing.coverage_threshold`, `testing.e2e_framework`, `workflow.ci_host`, `workflow.branch_protection`). Si una rama futura añade paths con `default:`, actualizar los 3 canonicals + `valid-partial` (mismo patrón).
- Snapshots por convención en `generator/__snapshots__/<slug>/<path>.snap`. +9 archivos añadidos en C5; total actual 54 (18 C1 + 9 C2 + 12 C3 + 6 C4 + 9 C5).
- Carry-over Fase N+7: **sin carry-over abierto** al arrancar D1.

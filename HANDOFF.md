# HANDOFF — quickref 30s

> Leer al arrancar sesión. Diseñado para llegar a "puedo ejecutar Fase -1 de la siguiente rama" en <1 minuto.

## 1. Snapshot

- Repo: `project-operating-system` (plugin `pos`).
- Fase actual: **C4 ✅ cerrada en rama** (`feat/c4-renderers-ci-cd`, PR pendiente de abrir). Anterior: **C3 ✅ PR #7** (`77d7e43`). Siguiente: **C5 — `feat/c5-renderers-skills-hooks-copy`**.
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

**C5 — `feat/c5-renderers-skills-hooks-copy`**

Scope (ver [MASTER_PLAN.md § Rama C5](MASTER_PLAN.md)):

- Renderers para copiar skills (`.claude/skills/pos/**`) + hooks (`hooks/**`) del meta-repo al proyecto generado, con customización de paths según el profile destino. Primer punto del pipeline donde `FileWrite` puede requerir el campo `mode` (hooks ejecutables = bit +x). Decidir en Fase -1 si extender el shape a `{ path, content, mode? }` o mantener binary bits fuera del manifiesto.
- Registrar nuevo array congelado (p.ej. `skillsHooksRenderers`) y componerse en `allRenderers`. 5ª aplicación del patrón `renderer-group`.

Lectura mínima al arrancar:

- [MASTER_PLAN.md § Rama C5](MASTER_PLAN.md)
- [docs/ARCHITECTURE.md § Renderers](docs/ARCHITECTURE.md) + [§ 4 Hooks](docs/ARCHITECTURE.md) + [§ 5 Skills](docs/ARCHITECTURE.md)
- [.claude/rules/generator.md](.claude/rules/generator.md) (Renderers + Deferrals) + [.claude/rules/templates.md](.claude/rules/templates.md) + [.claude/rules/skills-map.md](.claude/rules/skills-map.md)
- `generator/renderers/index.ts` + `generator/lib/render-pipeline.ts` (shape de `FileWrite`) + estructura de `.claude/skills/` + `hooks/` (aún vacíos; skills se pueblan en E, hooks en D — valorar si C5 copia sólo esqueleto o difiere la copia completa hasta D/E).

## 10. Estado C4 (cerrada en rama)

CI/CD workflow (`ci.yml`) + doc markdown `BRANCH_PROTECTION.md` emitidos por stack. 15 archivos por profile cuando `workflow.branch_protection == true` (14 si `false`): 6 docs + `policy.yaml` + 2 rules + 4 test harness + `ci.yml` + `docs/BRANCH_PROTECTION.md` opcional. Pipeline `allRenderers` compone `coreDocRenderers + policyAndRulesRenderers + testsHarnessRenderers + cicdRenderers` desde `generator/renderers/index.ts`. Detalle en [ROADMAP.md § Progreso Fase C](ROADMAP.md); pipeline documentada en [docs/ARCHITECTURE.md § Renderers](docs/ARCHITECTURE.md) + [§ 11 CI/CD integrado](docs/ARCHITECTURE.md#11-cicd-integrado).

Apuntes para quien arranque C5:

- Patrón `renderer-group` consolidado (4ª aplicación: core + policy/rules + tests-harness + ci-cd). C5 = 5ª aplicación — crear `skillsHooksRenderers` congelado y componerlo en `allRenderers`. `run.ts` no se toca.
- **Decisión abierta de C5**: `FileWrite` shape hoy es `{ path, content }`. Hooks ejecutables requieren bit `+x` → probable extensión a `{ path, content, mode? }`. Documentar la decisión en Fase -1 de C5 (decisión histórica prevista ya en C1/C2/C3/C4: "se añade en C5 si hooks ejecutables lo requieren").
- CI hosts no-github (`gitlab`, `bitbucket`) siguen diferidos. C5 no los reabre salvo señal explícita.
- `release.yml` / `audit.yml` / matrix multi-OS y multi-runtime siguen diferidos. Ramas propias futuras.
- Runtime version hardcoding (Node 20.17.0 / Python 3.11) en template C4 — si C5 toca paths de hooks que dependen de runtime, respetar la misma convención hasta que `stack.runtime_version` exista en schema.
- `buildProfile` sigue sin materializar defaults: `valid-partial` declara 4 paths explícitos hoy (`testing.coverage_threshold`, `testing.e2e_framework`, `workflow.ci_host`, `workflow.branch_protection`). Si C5 usa más paths con `default:`, actualizar los 3 canonicals + `valid-partial` (mismo patrón).
- Snapshots por convención en `generator/__snapshots__/<slug>/<path>.snap`. +6 archivos añadidos en C4; total actual 45 (18 C1 + 9 C2 + 12 C3 + 6 C4).
- Entry-point universal sigue siendo el `Makefile` emitido por C3. Los workflows invocan `make test-unit` + `make test-coverage`. Si C5 añade hooks ejecutables, valorar si se añaden targets al Makefile o se invocan directamente.
- Carry-over Fase N+7: **sin carry-over abierto** al arrancar C5.

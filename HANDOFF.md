# HANDOFF — quickref 30s

> Leer al arrancar sesión. Diseñado para llegar a "puedo ejecutar Fase -1 de la siguiente rama" en <1 minuto.

## 1. Snapshot

- Repo: `project-operating-system` (plugin `pos`).
- Fase actual: **C2 ✅ cerrada en rama** (`feat/c2-renderers-policy-rules`, PR pendiente de abrir). Anterior: **C1 ✅ PR #4** (`d361c9b`). Siguiente: **C3 — `feat/c3-renderers-tests-harness`**.
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

## 7. Gotchas del entorno

- El hook `pre-branch-gate.py` **aún no existe** (Fase D1). Hasta entonces, el marker es convención, no enforcement. Respetar manualmente.
- `policy.yaml` declarado pero no enforced todavía (Fase D4). Hasta entonces, docs-sync requiere disciplina manual.
- `/pos:*` skills no existen aún (Fase E*). Invocaciones fallarán silenciosas. Usar comportamiento manual equivalente.
- Todo hook declarado en `settings.local.json` con `_note: "Entregado en Fase D"` es un stub — el sistema tolera su ausencia.

## 8. Skills / subagents del entorno Claude Code (no plugin)

Hasta que `pos` tenga sus propias skills:

- `Explore` (>3 queries de búsqueda cross-archivo).
- `code-reviewer`, `code-architect`, `Plan` — subagents built-in.
- Skills globales del usuario (si las tiene en `~/.claude/skills/`).

## 9. Próxima rama

**C3 — `feat/c3-renderers-tests-harness`**

Scope (ver [MASTER_PLAN.md § Rama C3](MASTER_PLAN.md)):

- Renderer para test harness por stack (Node/Python/Go/Rust): configs (vitest/jest, pytest, go test, cargo), scripts en `package.json` / `Makefile`, ejemplo smoke test, `tests/README.md`.
- Registrarse en un nuevo array (p.ej. `testsHarnessRenderers`) y componerse en `allRenderers` desde `generator/renderers/index.ts` (patrón establecido en C2).

Lectura mínima al arrancar:

- [MASTER_PLAN.md § Rama C3](MASTER_PLAN.md)
- [docs/ARCHITECTURE.md § Renderers](docs/ARCHITECTURE.md)
- [.claude/rules/generator.md](.claude/rules/generator.md) + [.claude/rules/tests.md](.claude/rules/tests.md) + [.claude/rules/templates.md](.claude/rules/templates.md)
- `generator/renderers/index.ts` + `generator/lib/render-pipeline.ts` (patrón de composición entregado en C1/C2).

## 10. Estado C2 (cerrada en rama)

Policy + rules path-scoped emitidas. 9 archivos por profile (6 docs + `policy.yaml` + 2 rules). Pipeline `allRenderers` compone `coreDocRenderers + policyAndRulesRenderers` desde `generator/renderers/index.ts`. Detalle de entregables en [ROADMAP.md § Progreso Fase C](ROADMAP.md); pipeline documentada en [docs/ARCHITECTURE.md § Renderers](docs/ARCHITECTURE.md).

Apuntes para quien arranque C3:

- Patrón de composición: añadir un nuevo grupo de renderers = crear array congelado en `generator/renderers/index.ts` (p.ej. `testsHarnessRenderers`) y componerlo dentro de `allRenderers`. `run.ts` no se toca. Esto evita que `run.ts` se convierta en sitio de composición creciente.
- Colisiones de paths fallan el pipeline por invariante. `renderAll` reporta índices de los dos renderers que colisionan.
- Snapshots por convención en `generator/__snapshots__/<slug>/<path>.snap`. Añadir 1 template = 3 snapshots nuevos (uno por profile canónico). C3 presumiblemente añadirá varios templates por stack.
- Conditionals Handlebars del estilo `{{#if (eq answers.stack.language "typescript")}}` funcionan ya; `testing.unit.framework_node` / `framework_python` están resueltos en los 3 profiles canónicos.
- Helpers Handlebars se registran en `generator/lib/handlebars-helpers.ts`; si C3 necesita helpers stack-específicos, añadir tests de compilación real allí.
- Carry-over Fase N+7: **cerrado en C2**. No hay carry-over abierto al arrancar C3.

# HANDOFF — quickref 30s

> Leer al arrancar sesión. Diseñado para llegar a "puedo ejecutar Fase -1 de la siguiente rama" en <1 minuto.

## 1. Snapshot

- Repo: `project-operating-system` (plugin `pos`).
- Fase actual: **C1 en curso** (`feat/c1-renderers-core-docs`, PR por abrir). Anterior: **B3 ✅ PR #3** (`5388a80`). Siguiente: **C2 — `feat/c2-renderers-policy-rules`**.
- Fuente de verdad ejecutable: [MASTER_PLAN.md](MASTER_PLAN.md).
- Estado vivo: [ROADMAP.md](ROADMAP.md).
- Arquitectura canonical: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 2. Verificación de estado (1 comando)

```bash
git log --oneline -10 && git status -sb && ls .claude/branch-approvals/
```

Qué deberías ver:
- Último commit: bootstrap Fase A.
- Working tree limpio.
- `.claude/branch-approvals/` vacío (o con `.gitkeep`).

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

- **C1 (`feat/c1-renderers-core-docs`)** [parcial]: propagar Fase N+7 Context gate al repo generado en los 2 templates de su scope. `templates/HANDOFF.md.hbs` debe incluir la matriz de decisión + checklist post-merge; `templates/AGENTS.md.hbs` debe incluir Fase N+7 como última fase de rama en el flujo.
- **C2 (`feat/c2-renderers-policy-rules`)**: completa el carry-over. `templates/.claude/rules/docs.md.hbs` debe incluir el checkbox de trazabilidad (originalmente planeado en C1, diferido a C2 por coherencia de scope con `.claude/rules/*.md`). Todo proyecto generado con `pos` hereda la misma disciplina de context-management una vez C2 cierra.

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

**C2 — `feat/c2-renderers-policy-rules`**

Scope (ver [MASTER_PLAN.md § Rama C2](MASTER_PLAN.md)):

- Renderer para `policy.yaml` + `.claude/rules/*.md` según stack/paths del profile.
- Templates + helpers Handlebars adicionales (si el diseño lo exige).
- Completa el carry-over Fase N+7: `templates/.claude/rules/docs.md.hbs` con checkbox de trazabilidad (diferido desde C1 por coherencia de scope).

Lectura mínima al arrancar:

- [MASTER_PLAN.md § Rama C2](MASTER_PLAN.md)
- [docs/ARCHITECTURE.md § Renderers](docs/ARCHITECTURE.md)
- [.claude/rules/generator.md](.claude/rules/generator.md) + [.claude/rules/templates.md](.claude/rules/templates.md)
- `generator/renderers/` + `generator/lib/render-pipeline.ts` entregados en C1.

## 10. Estado C1 (en curso)

Objetivo: primera emisión real de archivos. Pipeline `Profile → FileWrite[] → fs`. 6 renderers puros + 6 templates Handlebars + wire-up `--out`/`--dry-run`.

Decisiones Fase -1 (aprobadas):

- **User-specific placeholders**: faltantes (`identity.name|description|owner`) → renderer emite literal `TODO(identity.<campo>)` + warning. Aplica a `--dry-run` y `--out`; no bloquea emisión.
- **Carry-over Fase N+7**: en C1 solo `HANDOFF.md.hbs` (matriz + checklist) y `AGENTS.md.hbs` (Fase N+7 en flujo). `docs.md.hbs` **diferido a C2**.
- **`--out` con subdirs** desde el primer día. `FileWrite.path` relativo + `mkdir -p`.
- **`FileWrite` shape**: `{ path: string; content: string }`. Sin `mode` (llega en C5).
- **`render-pipeline`** falla explícitamente ante colisión de paths (no solo detecta en tests).
- **Snapshots + tests semánticos**: snapshots por (profile × template) = 18, pero además tests unitarios por renderer verifican paths emitidos + strings críticas. Snapshots no son la única red de seguridad.
- **`--validate-only`** se conserva por compat/transición. Sin flags = comportamiento validate-only. `--force` fuera de scope (queda diferido).
- **Alternativas descartadas**: vertical slice (solo 2 templates) y "renderers sin wire-up CLI" — ambas fragmentarían la pipeline.

Archivos previstos:

- `generator/renderers/{claude-md,master-plan,roadmap,handoff,agents,readme}.ts` (+ `.test.ts` por cada uno).
- `generator/lib/handlebars-helpers.ts`, `generator/lib/render-pipeline.ts`, `generator/lib/profile-model.ts` (+ tests).
- `generator/run.ts` — wire-up `--out`/`--dry-run`.
- `templates/{CLAUDE.md,MASTER_PLAN.md,ROADMAP.md,HANDOFF.md,AGENTS.md,README.md}.hbs`.
- `templates/_partials/.gitkeep`.
- `generator/__snapshots__/<profile-slug>/*.snap` — 18 snapshots.
- CI: script `render:generator` + step en `.github/workflows/ci.yml`.

Deps nuevas: `handlebars` (única).

Commit 1 de la rama = **pre-kickoff chore**: docs-sync previo (ROADMAP B3→✅ PR #3 + C1→🔄 + Fase B→✅, HANDOFF §1/§9/§10, MASTER_PLAN §C1 decisiones Fase -1, §6b carry-over parcial) + kickoff block. **No parte funcional de renderers** — la implementación arranca en commit 2 con TDD estricto.

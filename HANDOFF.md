# HANDOFF — quickref 30s

> Leer al arrancar sesión. Diseñado para llegar a "puedo ejecutar Fase -1 de la siguiente rama" en <1 minuto.

## 1. Snapshot

- Repo: `project-operating-system` (plugin `pos`).
- Fase actual: **B3 en curso** (`feat/b3-generator-runner`, PR por abrir). Anterior: **B2 ✅ PR #2** (`f361c19`). Siguiente: **C1 — `feat/c1-renderers-core-docs`**.
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

- **C1 (`feat/c1-renderers-core-docs`)**: propagar Fase N+7 Context gate al repo generado. `templates/HANDOFF.md.hbs` debe incluir la matriz de decisión + checklist post-merge; `templates/AGENTS.md.hbs` debe incluir Fase N+7 como última fase de rama en el flujo; `templates/.claude/rules/docs.md.hbs` debe incluir el checkbox de trazabilidad. Todo proyecto generado con `pos` hereda la misma disciplina de context-management.

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

**C1 — `feat/c1-renderers-core-docs`**

Scope (ver [MASTER_PLAN.md § Rama C1](MASTER_PLAN.md)):

- Renderers para `CLAUDE.md`, `MASTER_PLAN.md`, `ROADMAP.md`, `HANDOFF.md`, `AGENTS.md`, `README.md`.
- Templates Handlebars correspondientes en `templates/`.
- Snapshot tests por renderer.
- Propagación Fase N+7 Context gate al repo generado (ver §6b carry-over).

Lectura mínima:

- [MASTER_PLAN.md § Rama C1](MASTER_PLAN.md)
- [docs/ARCHITECTURE.md § Generador](docs/ARCHITECTURE.md) + § Renderers.
- [.claude/rules/generator.md](.claude/rules/generator.md) + [.claude/rules/templates.md](.claude/rules/templates.md) (si existe).
- `generator/run.ts` + `generator/lib/` entregados en B3.

Checklist Fase -1 pendiente antes de abrir C1:

- [ ] Fase N+7 Context gate: decidir `continuar | /compact | /clear | sesión nueva` (ver §3).
- [ ] Resumen técnico ≤300 palabras.
- [ ] Resumen conceptual ≤150 palabras.
- [ ] Ambigüedades (si las hay).
- [ ] 2 alternativas evaluadas.
- [ ] Test plan.
- [ ] Docs plan.
- [ ] Aprobación explícita del usuario + marker `.claude/branch-approvals/feat_c1-renderers-core-docs.approved`.

## 10. Estado B3 (en curso)

Objetivo: primer código ejecutable del generador. Runner mínimo (profile YAML → zod-validado → completeness-checado → exit 0/1/2). Sin renderers — llegan en C*.

Decisiones Fase -1 (aprobadas):

- CLI args: `--profile <path>` (req) + `--validate-only`. `--out` y `--dry-run` rechazados con exit 2 y mensaje `flag --X not supported in B3; planned for C1`.
- Profile parcial con user-specific faltando (`identity.name`/`description`/`owner`) → exit 0 + warning. Otros required-missing → exit 1.
- Schema hard-coded a `questionnaire/schema.yaml`. `--schema` diferido.
- `generator/lib/schema.ts` re-exporta de `tools/lib/` (3ª aplicación pattern-before-abstraction; read-yaml fue la 2ª).
- `generator/lib/token-budget.ts` **diferido**: `schema.yaml` no declara `workflow.token_budget` todavía. Reintroducir cuando el campo exista.

Archivos previstos:

- `generator/run.ts`, `generator/lib/profile-loader.ts`, `generator/lib/schema.ts`, `generator/lib/validators.ts`.
- `generator/__fixtures__/profiles/{complete,partial-user-specific,invalid}/`.
- Tests unit por lib + integración CLI vía `spawnSync`. Coverage ≥85%.

Brechas heredadas de B2 (revisar si B3 las resuelve a coste marginal, si no re-diferir):

- `answer-value-not-in-array-allowlist` no validado a nivel instancia.
- `enum` con valor array/objeto emite `answer-value-not-in-enum` en vez de `answer-type-mismatch`.

Commit 1 de la rama = **pre-kickoff chore**: bundle de (a) context-gate hardening heredado de sesión previa (AGENTS.md regla #1 + §3 paso 3; HANDOFF.md §3 checklist) + (b) docs sync previo (ROADMAP B2→✅ PR #2 + B3→🔄, HANDOFF §1/§9/§10, MASTER_PLAN §B3 nota ajuste). **No parte funcional del runner B3** — la implementación arranca en commit 2 con TDD estricto.

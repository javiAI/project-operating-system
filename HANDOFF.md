# HANDOFF — quickref 30s

> Leer al arrancar sesión. Diseñado para llegar a "puedo ejecutar Fase -1 de la siguiente rama" en <1 minuto.

## 1. Snapshot

- Repo: `project-operating-system` (plugin `pos`).
- Fase actual: **B1 en curso** (`feat/b1-questionnaire-schema`, PR en apertura). Siguiente: **B2 — `feat/b2-profiles-starter`**.
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
- [ ] Elegir acción según la tabla: `continuar` | `/compact focus="..."` | `/clear` | sesión nueva.
- [ ] Si `compact` o `clear` o sesión nueva: **emitir resume prompt** con:
  - Archivos a releer (MASTER_PLAN § rama + "Contexto a leer" + schema/rules relevantes).
  - Decisiones ya tomadas que deben sobrevivir (shape, alternativa elegida, ambigüedades resueltas).
  - Tareas pendientes dentro de la rama nueva.
- [ ] Solo entonces proceder con Fase -1 (§2.1 MASTER_PLAN.md).
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

**B2 — `feat/b2-profiles-starter`**

Scope (ver [MASTER_PLAN.md § Rama B2](MASTER_PLAN.md)):

- `questionnaire/profiles/nextjs-app.yaml`, `agent-sdk.yaml`, `cli-tool.yaml`.
- Cada profile responde automáticamente ~60% del cuestionario.
- Fixture test en `generator/__fixtures__/profiles/` (carpeta no existe aún — se crea en rama).
- Criterio salida: los 3 profiles validan contra `questionnaire/schema.yaml` (B1).

Lectura mínima:

- [MASTER_PLAN.md § Rama B2](MASTER_PLAN.md)
- [questionnaire/schema.yaml](questionnaire/schema.yaml) — schema que deben cumplir.
- [docs/ARCHITECTURE.md § Cuestionario — Profiles predefinidos](docs/ARCHITECTURE.md)
- [.claude/rules/generator.md](.claude/rules/generator.md)

Checklist Fase -1 pendiente antes de abrir B2:

- [ ] Resumen técnico ≤300 palabras.
- [ ] Resumen conceptual ≤150 palabras.
- [ ] Ambigüedades (si las hay).
- [ ] 2 alternativas evaluadas.
- [ ] Test plan.
- [ ] Docs plan.
- [ ] Aprobación explícita del usuario + marker `.claude/branch-approvals/feat_b2-profiles-starter.approved`.

## 10. Estado B1 (cerrando)

Entregado en rama `feat/b1-questionnaire-schema`:

- `tools/validate-questionnaire.ts` + `tools/lib/{condition-parser,meta-schema,cross-validate}.ts`.
- `questionnaire/schema.yaml` (7 secciones A-G, 18 fields) + `questionnaire/questions.yaml` (22 preguntas con condicionales `when:`).
- `.github/workflows/ci.yml` (matrix ubuntu+macos, node 20, actions pineadas por SHA).
- `package.json`, `tsconfig.json`, `vitest.config.ts`, `.nvmrc` — toolchain TS + tsx + vitest + zod + yaml.
- 49 tests verdes, coverage 95.66% líneas, typecheck limpio.
- 6 commits: kickoff + parser + meta-schema + cross-validate + CLI/fixtures + questionnaire/docs.

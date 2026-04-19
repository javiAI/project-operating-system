# CLAUDE.md — project-operating-system (meta-repo)

> Reglas operativas del **propio meta-repo**. Para el sistema que este repo **genera** en otros proyectos, ver `templates/CLAUDE.md.hbs` (Fase C).

## Identidad

Este repo es un **plugin Claude Code** (`pos`) que:
1. Hace un cuestionario al usuario.
2. Produce un `project_profile.yaml`.
3. Genera un repo completo con hooks + skills + policy + CI/CD + test harness adaptado al stack.

No es una app runtime. No tiene servidor. Es un generador determinista + un plugin.

## Orden de lectura (si arrancas sesión nueva)

1. Este archivo (`CLAUDE.md`).
2. [AGENTS.md](AGENTS.md) — reglas de ejecución autónoma.
3. [HANDOFF.md](HANDOFF.md) — snapshot 30s.
4. [MASTER_PLAN.md § Rama actual](MASTER_PLAN.md) — sólo la sección de la rama en curso.
5. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — si necesitas el porqué de un diseño.

**NO** leas todo `MASTER_PLAN.md` ni docs enteros — cita por rangos. Path-scoped rules en [.claude/rules/](.claude/rules/) se cargan solas según los archivos que toques.

## Settings: shared vs local

- `.claude/settings.json` → **compartido** (committable). Hooks, permisos baseline, `claudeMdExcludes`.
- `.claude/settings.local.json` → **per-usuario** (gitignored). Overrides específicos del contribuyente (paths locales, binarios personales).

## Reglas no negociables

1. **Fase -1 antes de cada rama**. Sin `.claude/branch-approvals/<slug>.approved` no hay `git checkout -b`. Hook `pre-branch-gate.sh` lo enforza.
2. **Docs dentro de la rama**. ROADMAP, HANDOFF, AGENTS, rules/, patterns/ que se vean afectados se actualizan en el mismo PR que el código. Hook `pre-pr-gate.sh` bloquea PR sin docs-sync cuando aplica.
3. **Tests antes que implementación**. Para todo archivo en `generator/**` o `hooks/**`: primero test que falla, luego código que pasa. Hook `PreToolUse(Write)` lo enforza.
4. **Nunca `--no-verify`**, nunca `git reset --hard` sin confirmación explícita del usuario, nunca `git push --force` a `main`.
5. **Token budget declarado**. Ver [docs/TOKEN_BUDGET.md](docs/TOKEN_BUDGET.md). Este CLAUDE.md debe mantenerse <200 líneas; rules auto-cargadas <25KB combinadas.
6. **Community tools → `/pos:audit-plugin` obligatorio** antes de añadir cualquier MCP/plugin/skill no producida aquí. Ver [docs/SAFETY_POLICY.md](docs/SAFETY_POLICY.md).
7. **Patrones antes de abstraer**. ≥2 repeticiones documentadas en `.claude/patterns/` antes de crear helper compartido. Evita abstracción prematura.

## Stack y lenguajes

- **Generador**: TypeScript ejecutado con `tsx` (cero build step). Ver `generator/`.
- **Hooks**: Python 3.10+ (consistente con el ecosistema Claude Code).
- **Templates**: Handlebars (`.hbs`) — renderizados por el generador.
- **Tests del meta-repo**: `vitest` para generador; `pytest` para hooks; `bin/pos-selftest.sh` como integración end-to-end.
- **CI**: GitHub Actions (`.github/workflows/`).

## Comandos (cuando existan)

```bash
# Selftest end-to-end del plugin
./bin/pos-selftest.sh

# Generar un proyecto desde un profile
npx tsx generator/run.ts --profile questionnaire/profiles/nextjs-app.yaml --out /tmp/demo

# Ejecutar tests del generador
npx vitest run

# Ejecutar tests de hooks
pytest hooks/
```

## Flujo de rama (resumen; detalle en AGENTS.md)

```text
Fase -1  │ Aprobación (marker file)
Fase 0   │ Kickoff block (commit 1: scope + archivos + tests + docs plan)
Fase 1   │ Tests primero
Fase 2..N│ Implementación
Fase N+1 │ /pos:compress (si contexto >120k)
Fase N+2 │ /pos:pre-commit-review (context: fork)
Fase N+3 │ Docs-sync dentro de la rama (ROADMAP + HANDOFF + AGENTS + rules/patterns si procede)
Fase N+4 │ Pre-PR gate (hook valida: tests ✓, coverage ✓, docs-sync ✓, invariants ✓, CI-dry-run ✓)
Fase N+5 │ PR + CI en GitHub → merge
Fase N+6 │ /pos:compound (si el diff toca paths configurados; emite PR separado con patrones extraídos)
```

## Determinismo

Tres capas (detalle en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#determinismo)):
1. **Hooks** (no bypassables, exit code 2 o `permissionDecision: deny`).
2. **Logs** `.claude/logs/*.jsonl` — auditables por hooks posteriores.
3. **`/pos:audit-session`** — compara `policy.yaml` vs logs reales.

## Token efficiency — aplicación práctica aquí

- Este CLAUDE.md: **<200 líneas**. Detalle por dominio en `.claude/rules/*.md` con `paths:`.
- Skills pesadas (`/pos:pre-commit-review`, `/pos:compound`, `/pos:audit-session`) corren con `context: fork` + agent asignado → no contaminan el contexto principal.
- SessionStart hook imprime snapshot minimal de ROADMAP (no carga entero).
- Model routing (declarado en `policy.yaml`): Sonnet default, Opus sólo para skills de arquitectura, Haiku para lookups y compresión.

## Qué NO hacer en este repo

- No crear archivos `.md` de decisión/análisis fuera de `docs/` (use memory para eso).
- No añadir dependencias al generador sin justificarlas en el kickoff de la rama.
- No tocar `hooks/` y `generator/` en la misma rama — scope separado, PRs separados.
- No meter lógica en `CLAUDE.md` que corresponda a `.claude/rules/` path-scoped.
- No copiar contenido de `master_repo_blueprint.md` al código — el blueprint es referencia histórica, `docs/ARCHITECTURE.md` es la verdad actual.

## Skills activas (pobladas desde Fase E)

Ver [.claude/rules/skills-map.md](.claude/rules/skills-map.md) para mapa completo. En Fase A todavía no hay skills; esta sección crece cuando cada fase E* las entrega.

## Si algo bloquea

- Hook falla silencioso → revisa `.claude/logs/hooks.jsonl`.
- Marker no funciona → `.claude/branch-approvals/<slug>.approved` debe existir ANTES del `git checkout -b`.
- Pre-PR gate rechaza → lee el JSON del hook, te dice qué falta (docs-sync, test, invariant, CI-dry-run).
- No sabes dónde estás → `HANDOFF.md` + `git log --oneline -10`.

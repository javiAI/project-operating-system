---
name: ci-cd
description: Reglas al tocar workflows de CI/CD del meta-repo o templates de CI que el generador emite
paths:
  - ".github/workflows/**"
  - "templates/.github/**"
  - "generator/renderers/ci-cd.ts"
---

# Reglas — CI/CD

## Principio

**Nada merge-able sin CI verde. Nada en CI que no haya pasado local primero.**

El hook `pre-push.sh` corre la suite local; GitHub Actions corre la misma suite + matriz de entornos. Los dos deben estar alineados: si un check no existe local, no existe en CI, y viceversa.

## Workflows obligatorios (meta-repo)

1. **`.github/workflows/ci.yml`** — por PR y push a `main`. Entregado de forma incremental, rama a rama. La versión actual cubre:
   - **Aterrizado**: typecheck generator (`tsc --noEmit`), validación cuestionario + profiles, render generator dry-run, unit tests generator (vitest con coverage), unit tests hooks (pytest, matriz ubuntu + macos × Python 3.10/3.11), integración end-to-end (`pytest bin/tests` — smoke wrapper + 5 escenarios funcionales-críticos vía `bin/pos-selftest.sh`, ubuntu × Python 3.11) **(F3)**.
   - **Diferidos a rama dedicada** (declarados en `policy.yaml.pre_push.checks_required` como `command_meta`, no enforzados aún):
     - Lint + format check (`eslint`, `prettier`, `ruff`).
     - Typecheck hooks (`mypy hooks/`).
     - Snapshot diff check (valida templates deterministic).
   - **Invariante**: cuando una rama añade un check al workflow, también mueve su bullet de "Diferidos" a "Aterrizado" y ajusta el bloque `command_meta` en `policy.yaml` si procede.

2. **`.github/workflows/audit.yml`** — nightly + on-demand:
   - Re-corre `/pos:audit-plugin --self` en el propio repo.
   - Valida `policy.yaml` vs `.claude/logs/` (skills que deberían haber corrido).
   - Escanea dependencias con advisory database (`npm audit`, `pip-audit`).

3. **`.github/workflows/release.yml`** — en tag `v*` (entregado en F4):
   - Valida versión en `plugin.json` = tag.
   - Publica release en GitHub con bundle curated plugin-only.
   - Actualiza `javiAI/pos-marketplace` vía PR automático cuando `vars.POS_MARKETPLACE_REPO` está configurado (skippea silenciosamente si no — no bloquea release).

### Job `selftest` (entregado en F3)

Job dedicado a integración end-to-end del propio plugin `pos`. Corre en `ubuntu-latest` × Python 3.11 (sin matriz extendida — los gates funcionales que cubre son platform-agnostic y la generación del proyecto sintético es la operación más cara). Setup: Node (`npx tsx generator/run.ts`) + Python (`pytest bin/tests`). El comando único es `pytest bin/tests -q`, que ejecuta:

- **Smoke** (`bin/tests/test_selftest_smoke.py`): contrato del wrapper (`bin/pos-selftest.sh` existe, ejecutable, delega a `python3 bin/_selftest.py`, exit 0 al correr). Bloquea regresiones en la forma del entrypoint.
- **Scenarios** (`bin/tests/test_selftest_scenarios.py`): 5 escenarios funcionales-críticos contra un proyecto sintético generado por scenario:
  - **D1 pre-branch-gate** — deny `git checkout -b` sin marker → allow tras `touch <marker>`.
  - **D3 pre-write-guard** — deny `Write hooks/foo.py` sin test pair → allow tras crear `hooks/tests/test_foo.py`.
  - **D4 pre-pr-gate** — deny `gh pr create` sin docs-sync (ROADMAP + HANDOFF) en el diff → allow tras commit de docs.
  - **D5 post-action** — `git merge` confirmado por reflog cuyo diff matchea trigger emite advisory `Consider running /pos:compound`.
  - **D6 stop-policy-check** — Stop con `session_id` rogue (allowlist + `skills.jsonl` seeded) deniega; `session_id` clean allow.

**Out of scope** (ratificado en F3 Fase -1):

- D2 session-start (informative, exit 0 sin enforcement) y D6 pre-compact (informative). No tienen contrato deny/allow a verificar; el patrón se cubre vía sus tests unitarios en `hooks/tests/`.
- Claude Code runtime: el selftest no instancia Claude Code, no invoca skills/agents reales, no dispatchea `/pos:compound`. Skills/agents se verifican por presencia estática en sus tests dedicados.
- D5b loader: cubierto indirectamente — los hooks D3/D4/D5 lo consumen y los escenarios sobre-escriben `policy.yaml` del sintético para ejercitar el accessor live.

**Drift sintético ↔ meta-repo**: el `policy.yaml` que emite la generación cli-tool todavía tiene el shape pre-D5b (template no migrado). Cada escenario reescribe la sección que necesita (`pre_write` / `pre_pr` / `post_merge` / `skills_allowed`) directamente en `synthetic/policy.yaml`. Esto desacopla la cobertura de D5b de la migración del template (rama propia post-F3).

### Job `release` (entregado en F4)

Workflow dedicado [.github/workflows/release.yml](../../.github/workflows/release.yml). Trigger `push.tags: ['v*']`. Permissions `contents: write` para `gh release create`. Cinco jobs:

- **`version-match`** — primer gate. Asserta `plugin.json.version == ${tag#v}`. Sin esto, el resto no corre.
- **`selftest`** — reusa el contrato F3 (`pytest bin/tests -q`) sobre el repo en el ref del tag. Cubre los 19 nuevos contract tests de F4 (marketplace + release.yml shape + plugin version pin) más los 9 de F3.
- **`build-bundle`** — empaqueta `pos-v${version}.tar.gz` con scope plugin-only curated (`.claude-plugin/`, `.claude/skills/`, `.claude/rules/`, `hooks/`, `agents/`, `policy.yaml`, `bin/pos-selftest.sh`, `bin/_selftest.py`, `docs/RELEASE.md`). Sube como artifact con retention 30d.
- **`publish-release`** — `needs: [version-match, selftest, build-bundle]`. Descarga el artifact, llama `gh release create v${version} --generate-notes <bundle>`. **No** crea CHANGELOG.md enforced; usa autogenerated notes (decisión F4 — reabrir si patrón sale corto).
- **`mirror-marketplace`** — `if: vars.POS_MARKETPLACE_REPO != ''`. Clona el repo público, sincroniza `marketplace.json`, abre PR vía `gh`. Skippea silenciosamente cuando la variable está vacía (caso por defecto hoy, ya que `javiAI/pos-marketplace` no existe). Activación per-runbook [docs/RELEASE.md § Mirror al marketplace público](../../docs/RELEASE.md).

**Bundle curated, no repo entero**: el consumer del marketplace instala el plugin para usarlo. `generator/`, `tools/`, `templates/`, `questionnaire/`, `bin/tests/`, `.github/`, fixtures quedan fuera (ortogonales al runtime del plugin).

**Source of truth de versión**: `plugin.json.version`. Tag espeja (`v${version}`). `marketplace.json.plugins[0].source.ref` mirror-ea. Los tests `test_marketplace_json_schema.py` + `test_plugin_json_version_bump.py` cruzan los tres.

**Out of scope F4 (diferidos)**:

- `audit.yml` nightly (declarado en `policy.yaml.ci_cd.workflows` desde Fase A; sin consumer activo todavía).
- Skills `/pos:pr-description` y `/pos:release` (sin repetición demostrada — regla #7 CLAUDE.md).
- `CHANGELOG.md` enforced (autogenerated suffices hasta que falle).
- Creación efectiva del repo `javiAI/pos-marketplace` (manual cuando se decida ir live).

## Workflows generados (proyecto destino)

El generador emite workflows según `project_profile.yaml.git_host`. Soportados:

- `github` → `.github/workflows/*.yml`.
- `gitlab` → `.gitlab-ci.yml`.
- `bitbucket` → `bitbucket-pipelines.yml`.

Contenido adaptado al stack del profile (tests, lint, typecheck, coverage, preview deploy opcional).

## Reglas duras

1. **Sin secretos hardcoded**. Todo via `secrets.X`. El generador nunca emite un workflow con placeholder vacío que deje el secret expuesto.
2. **Workflows pinneados por SHA** (no `@v4`, sino `@<sha40>`). El generador produce pins; hook del meta-repo valida.
3. **Matriz mínima**: al menos 2 OS (ubuntu + macos) para generador; 2 versiones de runtime (Node 18/20, Python 3.10/3.11) para hooks.
4. **Coverage gate** en CI con threshold leído de `project_profile.yaml.testing.unit.coverage_threshold`. Fallo hace rojo el job.
5. **Branch protection rule** generada como doc markdown (`docs/BRANCH_PROTECTION.md`) — el usuario la aplica manualmente en GitHub settings. El generador no intenta llamar API de GitHub.

## Tests en CI que no existen local

Están prohibidos por esta rule. Si necesitas un check que requiere infra que no corre en dev (ej. secrets reales, servicios externos), documenta la razón en `.github/workflows/<file>.yml` en comentario del step + crea un test local equivalente con mocks.

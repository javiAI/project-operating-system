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

1. **`.github/workflows/ci.yml`** — por PR y push a `main`:
   - Lint + format check (eslint, prettier, ruff).
   - Typecheck (`tsc --noEmit` para generador; `mypy` para hooks).
   - Unit tests (vitest generador; pytest hooks).
   - Integración (`./bin/pos-selftest.sh`).
   - Snapshot diff check (valida templates deterministic).

2. **`.github/workflows/audit.yml`** — nightly + on-demand:
   - Re-corre `/pos:audit-plugin --self` en el propio repo.
   - Valida `policy.yaml` vs `.claude/logs/` (skills que deberían haber corrido).
   - Escanea dependencias con advisory database (`npm audit`, `pip-audit`).

3. **`.github/workflows/release.yml`** — en tag `v*`:
   - Valida versión en `plugin.json` = tag.
   - Publica release en GitHub con assets (plugin bundle).
   - Actualiza `javiAI/pos-marketplace` vía PR automático (cuando exista).

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

# RELEASE — runbook del plugin `pos`

> Cómo se versiona, empaqueta, publica y mirror-ea el plugin `pos` al marketplace público. Entregado en F4.

## Contrato de versionado

Una sola fuente de verdad: [`.claude-plugin/plugin.json`](../.claude-plugin/plugin.json) `version`.

- Git tag canonical = `v${version}` (ej. `v0.1.0`).
- `.claude-plugin/marketplace.json` `plugins[0].source.ref` = mismo tag.
- `.claude-plugin/marketplace.json` `plugins[0].version` (si presente) = mismo `${version}`.
- El test [bin/tests/test_plugin_json_version_bump.py](../bin/tests/test_plugin_json_version_bump.py) pin-ea el valor literal — bumpear requiere actualizar el test en el mismo commit (auto-documenta el milestone).
- El test [bin/tests/test_marketplace_json_schema.py](../bin/tests/test_marketplace_json_schema.py) cruza `marketplace.json` ↔ `plugin.json` — el sync se rompe en CI antes del tag.

Pre-1.0: API puede romper entre minors. F4 pinea `0.1.0` como primer release público; `1.0.0` queda para cuando Fase G aterrice o se decida estabilizar API explícitamente.

## Bundle del release

Asset adjunto a cada release: `pos-v${version}.tar.gz` con scope **plugin-only curated**.

Incluye:

- `.claude-plugin/` — `plugin.json`, `marketplace.json`.
- `.claude/skills/` — todas las skills publicadas.
- `.claude/rules/` — path-scoped rules.
- `hooks/` — hooks runtime.
- `agents/` — plugin subagents (`pos-code-reviewer`, `pos-architect`).
- `policy.yaml`.
- `bin/pos-selftest.sh` + `bin/_selftest.py` — selftest end-to-end del plugin instalado.
- `docs/RELEASE.md` — este runbook.

No incluye:

- `generator/`, `templates/`, `questionnaire/`, `tools/` — son meta-repo (cómo se generan proyectos), no plugin runtime.
- `bin/tests/` — test scaffolding del meta-repo.
- `.github/`, `docs/` (excepto `RELEASE.md`).

Razón: el consumer del marketplace instala el plugin para usarlo (skills + hooks + agents + policy + selftest). El generador del meta-repo es ortogonal.

## Flujo de release

### 1. Preparar el bump

En la rama de release (ej. `chore/release-0.2.0`):

1. Editar `.claude-plugin/plugin.json` → bump `version`.
2. Editar `.claude-plugin/marketplace.json` → sincronizar `plugins[0].source.ref` (`v${new}`) y `plugins[0].version`.
3. Editar [bin/tests/test_plugin_json_version_bump.py](../bin/tests/test_plugin_json_version_bump.py) → actualizar `EXPECTED_VERSION`.
4. Correr local: `pytest bin/tests -q` debe pasar.
5. Abrir PR. Pre-pr-gate exige docs-sync (ROADMAP + HANDOFF en el diff de la rama).
6. Merge a `main`.

### 2. Disparar el release

Tras merge a `main`:

```bash
git checkout main
git pull --ff-only
version=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])")
git tag -a "v${version}" -m "v${version}"
git push origin "v${version}"
```

GitHub Actions ejecuta [.github/workflows/release.yml](../.github/workflows/release.yml) automáticamente al detectar el tag.

### 3. Jobs del workflow

| Job | Qué hace | Falla si |
|---|---|---|
| `version-match` | Asserta `plugin.json.version == ${tag#v}`. | Drift entre tag y manifest. |
| `selftest` | `pytest bin/tests -q` (reusa el job F3 sobre proyecto sintético generado al vuelo). | Cualquier escenario D1/D3/D4/D5/D6 falla; cualquier contract test del marketplace/release/plugin.json rompe. |
| `build-bundle` | Empaqueta `pos-v${version}.tar.gz` con scope curated. Sube como artifact. | `tar` falla; algún path obligatorio falta. |
| `publish-release` | `needs: [version-match, selftest, build-bundle]`. Descarga el bundle, llama `gh release create v${version} --generate-notes <bundle>`. | Token inválido; tag duplicado; alguno de los `needs` rojo. |
| `mirror-marketplace` | Condicional `if: vars.POS_MARKETPLACE_REPO != ''`. Clona el repo público, actualiza `marketplace.json`, abre PR. | El repo público no existe / token mal configurado. **No bloquea el release** si la variable está vacía. |

### 4. Verificar el release

```bash
gh release view v${version}
gh release download v${version}
tar -tzf pos-v${version}.tar.gz | head -20
```

### 5. Recuperar de un release fallido

**Antes de `publish-release`** (`version-match`, `selftest` o `build-bundle` rojos):

```bash
git tag -d "v${version}"
git push origin ":refs/tags/v${version}"
```

Arregla el problema en `main` (PR nuevo) y re-tag.

**Después de `publish-release`** (release ya creado en GitHub):

```bash
gh release delete "v${version}" --yes
git tag -d "v${version}"
git push origin ":refs/tags/v${version}"
```

Ojo: si terceros ya descargaron el asset, eliminar no rebobina sus instalaciones. Considerar si en lugar de borrar conviene publicar `v${version}.1` con el fix.

## Mirror al marketplace público

El job `mirror-marketplace` espeja el `marketplace.json` local hacia `javiAI/pos-marketplace` (o el repo configurado vía `vars.POS_MARKETPLACE_REPO`). Está **condicional** porque ese repo público no existe todavía a fecha de F4.

Activarlo cuando exista:

1. Crear el repo público con un `marketplace.json` inicial (puede ser una copia de `.claude-plugin/marketplace.json`).
2. Configurar repo variable: `gh variable set POS_MARKETPLACE_REPO -b "javiAI/pos-marketplace"`.
3. Configurar secret con permiso `repo`: `gh secret set POS_MARKETPLACE_TOKEN -b "<PAT>"`.
4. El próximo release abre PR en el repo público automáticamente.

Hasta entonces, `mirror-marketplace` skippea silenciosamente (`if:` evalúa false → job marca skipped, release sale verde igual).

## Instalación user-facing (cuando el marketplace público exista)

```bash
# En Claude Code:
/plugin marketplace add javiAI/pos-marketplace
/plugin install pos
```

Claude Code resolverá `marketplace.json` → `plugins[0].source` → clonará `javiAI/project-operating-system` en el ref `v${version}` → activará skills + hooks + agents + policy del bundle instalado.

## Branch protection en el repo público

`docs/BRANCH_PROTECTION.md` aplica al **repo generado por `pos`**, no al meta-repo ni al marketplace público. Para el repo público recomendado:

- `main` protegido contra force-push.
- 1 reviewer requerido para PRs (incluido el bot del mirror).
- Status check `version-match` requerido si el repo público corre su propio CI.

Configurar manualmente vía GitHub Settings → Branches.

## Diferidos (no entregado en F4)

- `audit.yml` nightly — declarado en `policy.yaml.ci_cd.workflows[name=audit.yml]` desde Fase A; no aterrizado. Reabrir en rama propia post-F4 cuando consuma `npm audit` + `pip-audit` + `/pos:audit-plugin --self`.
- `/pos:pr-description` y `/pos:release` skills — listadas en [.claude/rules/skills-map.md](../.claude/rules/skills-map.md) como "entregado en F"; F4 entrega el flow manual antes de extraer skill (regla #7 CLAUDE.md: ≥2 repeticiones).
- `CHANGELOG.md` enforced — F4 usa `--generate-notes` de `gh release create` (autogenerado de commits + PRs). Reabrir si el patrón sale corto.
- Repo público `javiAI/pos-marketplace` — F4 deja la infraestructura local lista; la creación del repo público es manual cuando se decida ir live.

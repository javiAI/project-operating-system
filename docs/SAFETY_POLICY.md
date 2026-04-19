# SAFETY_POLICY — community tool vetting

> Política vinculante. Implementada por `/pos:audit-plugin` (Fase E2b). Antes de esa skill, seguir este checklist a mano.

## Principio

Aprovechar la comunidad sin introducir troyanos ni malware. Todo tool externo pasa por gate.

## Fuentes confiables (ranked)

| Nivel | Fuente | Confianza | Ejemplo |
|---|---|---|---|
| 1 | Anthropic MCP registry | Pre-auditado | `mcp-registry/*` |
| 2 | Plugins `@anthropics/*` | Oficial | — |
| 3 | Autores verificados | Manual | MemPalace, PleasePrompto |
| 4 | Otros | Case-by-case | Audit full obligatorio |

**Autor verificado** = repo con ≥500 stars, mantenimiento activo últimos 6 meses, código abierto completo, historial público del mantenedor (no cuenta recién creada).

## Checklist de auditoría

Obligatorio antes de `allow`. Resultado archivado en `.claude/logs/audits/<tool>-<version>.md`.

### 1. Manifest review

- [ ] `plugin.json` / `skill.md` frontmatter leído entero.
- [ ] Versión pineada (no `latest`, no rango flexible).
- [ ] Licencia compatible (MIT, Apache-2, BSD-3, ISC).
- [ ] Homepage/repo URL accesible públicamente.
- [ ] Changelog o release notes disponibles.

### 2. Hooks inspection

Para cada hook declarado:

- [ ] Sin `curl`, `wget`, `ssh`, `scp` en comandos.
- [ ] Sin `eval`, `exec` con input no-sanitizado.
- [ ] Sin lectura de paths sensibles: `.env`, `~/.ssh/`, `~/.aws/`, `~/.gnupg/`.
- [ ] Sin escritura fuera del repo del proyecto.
- [ ] Sin `subprocess.run(..., shell=True)` con input externo.
- [ ] Sin binarios empaquetados sin source correspondiente.

### 3. MCP server inspection

Si el tool incluye MCP server:

- [ ] Args declarados (no flags hidden).
- [ ] Env vars requeridos documentados.
- [ ] Sin credenciales hardcoded.
- [ ] Network endpoints declarados (host + puerto).
- [ ] Scope de tools expuestos explicito (no `*`).
- [ ] Si usa browser automation / cookie scraping → **rechazar** salvo excepciones documentadas (ej. `PleasePrompto/notebooklm-mcp` con auth persistente, no cookies manuales).

### 4. Permissions

- [ ] `allowed-tools:` es subset mínimo necesario.
- [ ] Un skill de linting no tiene `Write(~/**)`.
- [ ] Un skill de review no tiene `Bash(git push)`.
- [ ] `paths:` frontmatter limita scope cuando aplicable.

### 5. Runtime footprint

- [ ] Dependencias declaradas y auditadas (`npm audit`, `pip-audit`).
- [ ] Sin network calls en install (no post-install scripts que descargan).
- [ ] Tamaño razonable para el scope declarado.

### 6. Versioning + pin

- [ ] Versión exacta anotada en `.claude/plugins.lock`.
- [ ] SHA commit registrado (no sólo tag).
- [ ] Diff vs última versión revisada si es upgrade.

## Denylist vigente

Con razón documentada:

| Tool | Razón |
|---|---|
| `openclaw-claude-code` | Palo Alto Networks lo describió como "biggest insider threat 2026". Gary Marcus: "disaster waiting to happen". |
| `notebooklm-mcp-cli` (jacob-bd) | Usa APIs privadas no documentadas de NotebookLM. Requiere extracción manual de cookies del navegador. Declarado "personal/experimental" por el autor. Alternativa segura: `PleasePrompto/notebooklm-mcp`. |

## Allowlist inicial (starter opt-in)

Se activan via flag en `project_profile.yaml`:

| Tool | Flag | Riesgo | Razón approval |
|---|---|---|---|
| `MemPalace/mempalace` | `memory.persistent: true` | Bajo | MIT, local-first, 96.6% recall LongMemEval, sin network calls en retrieval, hook auto-save opcional. |
| `PleasePrompto/notebooklm-mcp` | `research.notebooklm: true` | Medio | MIT, auth persistente (no cookies manuales), research grounded para Claude. Requires Google account user-controlled. |

Cualquier otro tool → checklist completo via `/pos:audit-plugin`.

## Denial → apelación

Si `/pos:audit-plugin` deniega:

1. Usuario revisa el log de audit (`.claude/logs/audits/<tool>-<version>.md`).
2. Si el fallo es subsanable por el mantenedor del tool: abrir issue upstream.
3. Si es falso positivo: documentar en `docs/AUDIT_APPEALS.md` con evidencia + override explícito en `policy.yaml.safety.community_tool_gate.approved_overrides`. Segunda opinión humana requerida.

## Re-audit

- Anual por default.
- Inmediato si el tool sube mayor versión.
- Inmediato si CVE publicado (hook `audit.yml` nightly verifica advisory DB).

## Relación con `policy.yaml`

`policy.yaml.safety.community_tool_gate`:

- `block_install_without_pass: true` — hook `PreToolUse(Bash)` bloquea `npm install <tool>` si el tool no está en allowlist.
- `trusted_sources` — lista de namespaces permitidos.
- `denylist` — duros.

## Testing del gate

`bin/pos-selftest.sh` escenario `install-blocked-by-denylist`:
- Simula intento de instalar tool en denylist.
- Verifica hook emite `permissionDecision: deny`.
- Falla el selftest si pasa.

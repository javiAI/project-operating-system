# KNOWN_GOOD_MCPS — allowlist opt-in

> MCPs evaluados y aprobados para uso opt-in en proyectos generados. Cualquier otro requiere `/pos:audit-plugin` pass.

## Formato

```
## <namespace>/<nombre>
- Versión auditada: <x.y.z> (SHA: <hash>)
- Licencia: <tipo>
- Riesgo: <low | medium | high>
- Profile flag: `<ruta.del.flag>`
- Uso recomendado: <descripción corta>
- Restricciones: <cualquier caveat>
- Última re-audit: <YYYY-MM-DD>
```

---

## MemPalace/mempalace

- **Versión auditada**: 0.4.x (pendiente SHA al instalar por primera vez).
- **Licencia**: MIT.
- **Riesgo**: Low.
- **Profile flag**: `memory.persistent: true`
- **Uso recomendado**:
  - Proyectos con >6 meses de duración.
  - Equipos con alta rotación de sesiones Claude.
  - Casos donde el auto-memory nativo (`~/.claude/projects/<project>/memory/`) no basta.
- **Capacidades**:
  - MCP server con 29 tools (palace reads/writes, knowledge-graph, agent management).
  - Auto-save hook periódico + pre-context-compression.
  - Almacena conversación verbatim sin resumir.
  - ChromaDB backend por defecto (local).
  - Recall 96.6% en LongMemEval sin API calls.
- **Restricciones**:
  - ~300 MB disco para embedding model default.
  - No recomendado para proyectos <3 meses (overhead > beneficio).
  - No usar `mempalace mine` sobre `.env`, `.git/`, `node_modules/`.
- **Checklist de audit completado**: sí (Fase A, pre-installation).
- **Última re-audit**: 2026-04-19.

---

## PleasePrompto/notebooklm-mcp

- **Versión auditada**: 1.x.x (pendiente SHA).
- **Licencia**: MIT.
- **Riesgo**: Medium (depende de NotebookLM API + auth Google del usuario).
- **Profile flag**: `research.notebooklm: true`
- **Uso recomendado**:
  - Proyectos con research estructurado previo en NotebookLM.
  - Workflows donde Claude genera código basado en docs citadas con source-grounding.
  - Proyectos de consultoría / análisis.
- **Capacidades**:
  - Claude Code puede query notebooks de NotebookLM.
  - Citas con source-grounding (reduce alucinaciones).
  - Auth persistente (no requiere scraping de cookies manual).
  - Library management + cross-client sharing.
- **Restricciones**:
  - Requiere cuenta Google controlada por el usuario.
  - Rate limit ~50 queries/día en free tier.
  - NotebookLM puede cambiar APIs sin notice (monitorear upstream).
  - Usa browser automation — revisar cada upgrade.
- **Alternativas rechazadas**:
  - `jacob-bd/notebooklm-mcp-cli` → denylist por scraping manual de cookies + APIs privadas no documentadas.
- **Checklist de audit completado**: sí (Fase A).
- **Última re-audit**: 2026-04-19.

---

## Cómo añadir un nuevo MCP a esta lista

1. Invocar `/pos:audit-plugin <repo-url>` (cuando exista, Fase E2b).
2. Checklist de `docs/SAFETY_POLICY.md` completo.
3. Añadir entrada aquí + en `policy.yaml.safety.community_tool_gate.optin_starter_mcps`.
4. Añadir flag correspondiente en `questionnaire/schema.yaml`.
5. Emitir PR. Hook `pre-pr-gate.py` valida que los 4 puntos están sincronizados.

## Denylist de referencia

Ver `docs/SAFETY_POLICY.md#denylist-vigente`. No replicar aquí para evitar drift.

# TOKEN_BUDGET — reglas de eficiencia

> Presupuesto declarativo + técnicas aplicadas. Enforced por hooks (Fase D) y validado por `/pos:audit-session` (Fase F1).

## Presupuesto (del `policy.yaml`)

| Métrica | Valor |
|---|---|
| `session_soft_limit` | 150000 tokens |
| `session_hard_limit` | 180000 tokens |
| `warn_at` | 120000 — SessionStart emite aviso |
| `auto_compact_at` | 160000 — Stop hook fuerza `/compact` |
| `claude_md_max_lines` | 200 líneas |
| `rules_total_max_kb` | 40KB combinados en `.claude/rules/` (incluye archivos de referencia con `paths: []`) |
| `rules_autoload_max_kb` | 25KB suma de rules con `paths:` no-vacío (las que entran automáticamente a contexto) |

Violación de cualquier límite → warning (soft) o bloqueo (hard), según hook.

## Técnicas aplicadas (ranking por impacto)

### 1. `.claude/rules/*.md` path-scoped (~40-60% ahorro en base context)

`CLAUDE.md` root ≤200 líneas con reglas universales. Detalle por dominio en `rules/*.md` con frontmatter `paths:`. Claude Code carga un rule solo cuando toca archivos matching.

```yaml
---
paths: ["src/app/api/**"]
---
```

**Caveat conocido** (issue #16853, #23478): algunas versiones cargan rules solo en Read, no en Write. Hook `PreToolUse(Write)` inyecta el contenido como `additionalContext` como workaround (Fase D3).

### 2. Skills con `context: fork` (20-40k tokens/invocación)

Skills pesadas (review, audit, compound, simplify) corren en subagente. El output estructurado vuelve al main context. El análisis intermedio queda en el fork.

Aplica a: `/pos:pre-commit-review`, `/pos:simplify`, `/pos:compound`, `/pos:audit-*`, `/pos:compress`.

No aplica a: `/pos:kickoff`, `/pos:handoff-write` (latencia interactiva importa más).

### 3. SessionStart snapshot minimal (~5-10k tokens/sesión)

`hooks/session-start.py` (Fase D2) emite:
- Rama actual.
- Últimos 3 commits.
- Fase en curso (parsea ROADMAP).
- Warnings de sesión anterior (si las hay en `.claude/logs/`).

**No** carga HANDOFF.md entero. No carga MASTER_PLAN.md. El usuario/Claude los lee bajo demanda.

### 4. `/pos:compress` skill (principio Caveman)

Skill `context: fork`, model: haiku, que comprime:
- Docs de ≥1000 líneas → resumen estructurado.
- Logs de tool output ≥500 líneas.
- Research citado por rango.

Preserva código textual, URLs, paths de archivos. Compresión medida 30-50%.

### 5. Model routing (3-5× reducción de costo)

Declarativo en `policy.yaml.model_routing`:

- **Haiku** (barato): compresión, lookups, coverage-explain, extracciones simples.
- **Sonnet** (default): review, generación, planning estándar.
- **Opus** (caro, preciso): arquitectura (branch-plan, deep-interview), compound, refactors cross-módulo.

Skills declaran modelo en frontmatter. Hook `PreToolUse` (Fase D) valida que no se use opus sin justificación.

### 6. Auto-compact managed (para scripts `claude -p` generados)

Cuando el generador produce CI/scripts que invocan `claude -p`, incluye flags:

```bash
claude -p --context-management=compact_20260112 --tool-management=clear_tool_uses_20250919 ...
```

Esto mantiene sesiones largas de CI sin reiniciar.

### 7. Tool-result clearing (~20-30% en sesiones con muchos reads)

`clear_tool_uses_20250919` — Claude Code descarta resultados de tool calls antiguos cuando el contexto se aproxima al límite. Configurado por default en scripts generados.

### 8. Path-scoped patterns (reemplaza cargar todos los patterns globalmente)

Los archivos en `.claude/patterns/**` tienen `paths:` en frontmatter. Sólo se inyectan cuando Claude toca archivos matching. Hook Fase D3 lo implementa (por bug #16853 antes mencionado).

### 9. Memoria persistente opt-in

- **Auto-memory nativo de Claude Code** (`~/.claude/projects/<project>/memory/`) activo por default.
- **MemPalace** opt-in para proyectos >6 meses o con alta rotación de sesiones.

Evita re-explicación cross-session. Ver `docs/SAFETY_POLICY.md` antes de activar MemPalace.

### 10. Subagents aislados para research (50-80k en ramas de research)

Para investigaciones cross-archivo, invocar subagent `Explore` o `code-explorer`. Devuelven report estructurado. El main context no carga cada Read/Grep.

## Token budget per-project (profile)

El generador emite `token_budget` en el `policy.yaml` del proyecto destino. Default = mismo que meta-repo. Override en profile:

```yaml
token_budget:
  session_soft_limit: 200000  # proyecto grande
  auto_compact_at: 180000
  claude_md_max_lines: 150    # más estricto
```

## Monitoreo

- `/context` (built-in Claude Code) — vista actual de tokens usados por categoría.
- `.claude/logs/context-usage.jsonl` — el hook `Stop` loguea (Fase D6) uso final de cada turno.
- `/pos:audit-session` report incluye histograma de consumo por sesión.

## Anti-patrones (hook bloquea en Fase D3)

- Cargar `master_repo_blueprint.md` en una sesión de implementación (exceso de context histórico).
- `Read` sin `offset`/`limit` a archivos >1500 líneas cuando sólo se necesita una sección.
- Múltiples `Grep` con regex abiertas ("." o "^$") que devuelven todo.
- Pegar stacktraces enteros cuando bastaba el error principal + 5 líneas de contexto.
- Loggear diff binario o minified JS en mensajes de error.

## Acciones al superar umbrales

| Umbral | Acción automática |
|---|---|
| `warn_at` (120k) | SessionStart emite aviso al siguiente turno |
| `auto_compact_at` (160k) | Stop hook fuerza `/compact` con focus en decisiones in-flight |
| `session_hard_limit` (180k) | Bloqueo de Write/Edit hasta que se haga `/compact` o `/clear` |

## Revisión

`/pos:audit-session` incluye review de token budget. Si el presupuesto se viola consistentemente (>30% sesiones al mes):

1. Evaluar si CLAUDE.md + rules creció too much → split o purge.
2. Evaluar si alguna skill pesada debería migrar a `context: fork`.
3. Evaluar si `SessionStart` está cargando demasiado.

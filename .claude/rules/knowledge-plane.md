# Reglas — Knowledge Plane

## Paths cubiertos

```yaml
paths:
  - "templates/vault/**"   # meta-repo: archivos fuente de la capa (G2+)
  - "vault/**"             # proyecto generado: vault real cuando pos se usa
```

`templates/vault/**` aplica al meta-repo cuando se trabaja en G2+ (renderers,
templates `.hbs`). `vault/**` aplica cuando Claude Code opera dentro de un proyecto
generado por `pos` que tiene la capa activada.

## Contrato de referencia

Ver [docs/KNOWLEDGE_PLANE.md](../../docs/KNOWLEDGE_PLANE.md) para el contrato
completo (tres capas, principios invariantes, scope de cada rama G1–G4).

## Qué hacer al editar archivos bajo `vault/**`

1. **Respetar la separación raw / wiki / config.md**. No mover contenido de `raw/`
   a `wiki/` sin síntesis; no modificar `raw/` in-place (son fuentes inmutables).

2. **`vault/config.md` es la fuente de verdad local**. Antes de añadir convenciones
   de nomenclatura o tags, verificar que no contradicen `vault/config.md`.

3. **Sin dependencias de runtime**. Ningún archivo del vault debe importar, requerir
   ni referenciar código ejecutable. El vault es solo Markdown.

4. **Sin nuevos campos del questionnaire** sin rama G propia. Si una tarea requiere
   ampliar el opt-in (ej. `integrations.knowledge_plane.adapter`), seguir el flujo
   de rama con Fase -1 explícita. No añadir campos al schema.yaml directamente
   (regla #7 CLAUDE.md — ≥2 repeticiones antes de abstraer).

## Qué hacer al editar archivos bajo `templates/vault/**` (meta-repo, G2+)

1. **TDD obligatorio** para cualquier nuevo renderer en `generator/renderers/`.
   El pre-write-guard enforza test-pair co-located para `generator/**/*.ts`.

2. **Registrar el renderer** en `generator/renderers/index.ts` dentro del grupo
   `knowledgePlaneRenderers` (nuevo grupo, patrón `renderer-group` — sexta aplicación
   del patrón; los 5 grupos existentes son core/policy/tests/cicd/skills-hooks, ver
   `.claude/rules/generator.md § Renderers`).

3. **Snapshots deterministas**: el renderer no debe usar `Date.now()` ni rutas del
   host. El timestamp se inyecta vía `profile.metadata.generatedAt`.

4. **Opt-in gate**: el renderer sólo emite archivos cuando
   `answers["integrations.knowledge_plane.enabled"] === true`. Con `false` (default),
   la función devuelve `[]`.

## Qué NO hacer

- No implementar ingest automático, daemons ni watchers dentro del vault (G3 es stub CLI manual).
- No añadir MCP específico de Obsidian como dependencia del meta-repo (es reference adapter, no contrato base).
- No crear `vault/schema.md` — el config file se llama `vault/config.md` (decisión G1, evita colisión léxica con `questionnaire/schema.yaml`).
- No mezclar renderer de vault con otros renderers en una misma rama. Scope separado (CLAUDE.md "No tocar hooks/ y generator/ en la misma rama").

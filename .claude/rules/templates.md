---
name: templates
description: Reglas cuando editas templates Handlebars que el generador renderiza en proyectos destino
paths:
  - "templates/**"
---

# Reglas — Templates Handlebars

## Naming

- `templates/<path-relativo-al-proyecto-generado>.hbs`. Ejemplo: `templates/CLAUDE.md.hbs` → `CLAUDE.md` en el proyecto generado.
- `templates/.github/workflows/ci.yml.hbs` → `.github/workflows/ci.yml`.
- Archivos que dependen de flags del profile: sufijo `.optional.hbs` → el renderer decide si emitirlo.

## Sintaxis

- Handlebars estándar. Nada de lógica compleja en template — helpers registrados en `generator/lib/handlebars-helpers.ts`.
- Helpers disponibles: `{{#if}}`, `{{#each}}`, `{{#unless}}`, `{{#with}}`, más custom: `{{eq}}`, `{{neq}}`, `{{includes}}`, `{{kebabCase}}`, `{{upperFirst}}`, `{{jsonStringify}}`.

## Reglas duras

1. **Nada hardcoded** que deba variar entre profiles — todo via `{{profile.xxx}}`.
2. **Comentarios del template** empiezan con `{{!-- ... --}}` y son stripped del output.
3. **Frontmatter YAML** dentro de un template: escapar `{{` → `\{{ }} \}}` si literal, no interpolación.
4. **Newlines finales**: cada template termina en `\n`.
5. **Placeholder sin valor** → error del generador (strict mode), no output silencioso vacío.

## Tests

- Snapshot por profile: render de cada template con cada profile predefinido → output guardado en `generator/__snapshots__/<profile>/<path>.snap`.
- Si el snapshot cambia, el PR debe explicarlo en el kickoff.

## Patrones a seguir

- Una template = una responsabilidad. Si `CLAUDE.md.hbs` necesita lógica condicional compleja, parte en `CLAUDE.md.hbs` + `CLAUDE.<profile>.hbs` + wrapper en renderer.
- Prefiere incluir fragments via `{{> partial-name}}` para secciones reutilizables (disclaimer de Liora-style replatform, sección de CI/CD, sección de policy, etc.).

## Fragmentos reutilizables

Ubicación: `templates/_partials/`. Ejemplos:

- `_partials/ci-github.hbs`
- `_partials/ci-gitlab.hbs`
- `_partials/test-harness-node.hbs`
- `_partials/test-harness-python.hbs`
- `_partials/policy-skills-stock.hbs`

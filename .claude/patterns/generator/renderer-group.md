---
name: renderer-group
description: Cómo añadir un grupo cohesivo de renderers al generador sin ensuciar `run.ts` — array congelado por dominio + composición en `index.ts`.
area: generator
status: active
extracted_at: 2026-04-21
evidence:
  - commit: d361c9b
    branch: feat/c1-renderers-core-docs
    pr: 4
    note: "Introdujo `coreDocRenderers` como frozen tuple en `generator/renderers/index.ts` con los 6 renderers de core docs (CLAUDE, MASTER_PLAN, ROADMAP, HANDOFF, AGENTS, README)."
  - commit: 694f5bc
    branch: feat/c2-renderers-policy-rules
    pr: 5
    note: "Añadió `policyAndRulesRenderers` (frozen tuple con policy.ts + rules.ts) y `allRenderers = Object.freeze([...coreDocRenderers, ...policyAndRulesRenderers])`. `run.ts` importa sólo `allRenderers`."
---

# Pattern — `renderer-group`

## Qué es

Cuando un grupo de renderers comparte dominio (core docs, policy/rules, test harness, CI/CD, copia de skills/hooks), **exponerlo como `readonly Renderer[]` congelada en [generator/renderers/index.ts](../../../generator/renderers/index.ts) y componerlo dentro de `allRenderers`**. El runner (`generator/run.ts`) importa únicamente `allRenderers`.

## Por qué

- **`run.ts` no crece por fase.** Cada rama C* añade renderers sin tocar el runner. Si la composición viviera en `run.ts`, el runner se convertiría en el único punto de merge-conflict por fase y su diff crecería por acumulación.
- **Frozen array = invariante runtime.** `Object.freeze` impide mutaciones accidentales (push a un array global, spread mal escrito, etc.). Los tests lo verifican con `Object.isFrozen(X) === true`.
- **Agrupación por dominio = legibilidad.** El lector que llega a `index.ts` ve qué familias de renderers existen antes de leer ninguna de ellas. Navegación por grupos, no por lista plana.
- **Pipeline invariante de colisión.** `renderAll` falla si dos renderers emiten el mismo path — si un grupo nuevo colisiona con uno existente, los tests de composición lo detectan inmediatamente.

## Cómo aplicar

### 1. Crear renderers individuales

Cada uno exporta una función pura `(profile: Profile) => FileWrite[]`:

```ts
// generator/renderers/<grupo>-<nombre>.ts
import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const template = loadTemplate("<ruta-al-template>.hbs");

export const render: Renderer = (profile: Profile): FileWrite[] => [
  { path: "<ruta-relativa-output>", content: template(profile) },
];
```

### 2. Exponer el grupo como frozen tuple en `index.ts`

```ts
// generator/renderers/index.ts
import { render as renderA } from "./<grupo>-a.ts";
import { render as renderB } from "./<grupo>-b.ts";

export const <grupo>Renderers: readonly Renderer[] = Object.freeze([
  renderA,
  renderB,
]);
```

### 3. Componer dentro de `allRenderers`

```ts
export const allRenderers: readonly Renderer[] = Object.freeze([
  ...coreDocRenderers,
  ...policyAndRulesRenderers,
  ...<grupo>Renderers,  // ← nuevo grupo aquí, sin tocar run.ts
]);
```

### 4. Tests mínimos en `index.test.ts`

```ts
describe("renderers/index — <grupo>Renderers (Cx)", () => {
  it("exposes exactly N renderers (Cx scope)", () => {
    expect(<grupo>Renderers).toHaveLength(N);
  });

  it("is frozen to prevent accidental mutation", () => {
    expect(Object.isFrozen(<grupo>Renderers)).toBe(true);
  });
});
```

Los tests de composición (paths emitidos a través de `renderAll(profile, [...allRenderers])`) validan implícitamente que el nuevo grupo no colisiona con los anteriores.

## Qué evita

- **`run.ts` convertido en sitio de composición creciente.** En C2 la Fase -1 rechazó explícitamente `[...coreDocRenderers, ...policyAndRulesRenderers]` inline en `run.ts` por este motivo.
- **Array mutable global.** Un `const renderers: Renderer[] = [...]` sin freeze permite `renderers.push(x)` desde cualquier import — rompe determinismo.
- **Agrupación plana sin dominio.** Un único array `allRenderers = [r1, r2, ..., rN]` creciendo linealmente pierde la señal de agrupación por fase.

## Señales de que debería bifurcarse

Reabrir este pattern si aparece una de estas señales:

- Un grupo necesita composición condicional por profile (p.ej. `testsHarnessRenderers` que depende del stack). Solución previsible: un factory `buildTestsHarnessRenderers(profile)` devolviendo el array, invocado desde `allRenderers` tras resolver profile. El freeze se aplica al resultado.
- Dos grupos necesitan ordenación relativa (p.ej. CI/CD debe emitir después de policy porque referencia sus paths). Documentar orden en `index.ts` como comentario + test que lo asserta.

## Enlaces

- [generator/renderers/index.ts](../../../generator/renderers/index.ts) — composición actual.
- [generator/lib/render-pipeline.ts](../../../generator/lib/render-pipeline.ts) — `renderAll` y contrato `Renderer`.
- [docs/ARCHITECTURE.md § 3 Renderers](../../../docs/ARCHITECTURE.md) — contexto arquitectónico.
- [.claude/rules/generator.md](../../rules/generator.md) — regla path-scoped con detalle.

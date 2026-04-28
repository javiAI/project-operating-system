# KNOWLEDGE_PLANE — Especificación del contrato

> Contrato tool-agnostic de la capa knowledge plane opcional del plugin `pos`.
> Para contexto arquitectónico y posición en el modelo de dos capas del meta-repo,
> ver [docs/ARCHITECTURE.md § 1.1](ARCHITECTURE.md#11-knowledge-plane-opcional).

## 1. Qué es el knowledge plane

El knowledge plane es una capa opcional que puede activarse en cualquier repo generado
por `pos` vía el opt-in del questionnaire. No forma parte del control plane (meta-repo)
ni del runtime plane (proyecto generado base): es una extensión mountable que provee
estructura para gestionar conocimiento de proyecto en Markdown plano.

**Opt-in**: `integrations.knowledge_plane.enabled: true` en el profile del proyecto.
Con el flag en `false` (default), el generador no emite nada de esta capa.

## 2. Las tres capas

```
vault/
├── raw/          fuentes inmutables
├── wiki/         síntesis
└── config.md     configuración de la instancia
```

### 2.1 `vault/raw/` — fuentes inmutables

Contiene material de referencia que no se reescribe: artículos, papers, transcripciones,
notas importadas, clippings web. Las entradas se añaden, nunca se modifican en el lugar.

**Convenciones**:
- Un archivo por fuente. Nombre descriptivo en kebab-case (`2024-attention-is-all-you-need.md`).
- Incluir metadatos mínimos al inicio del archivo: `source:`, `date:`, `tags:` (sin schema forzado).
- No crear subdirectorios sin criterio establecido en `vault/config.md`.

### 2.2 `vault/wiki/` — síntesis

Contiene conocimiento procesado: resúmenes, decisiones de diseño, conceptos clave,
glosarios, relaciones entre fuentes. Mantenida por el LLM o por el humano; puede
reescribirse cuando el conocimiento evolucione.

**Convenciones**:
- Páginas en kebab-case (`arquitectura-hooks.md`, `decisiones-auth.md`).
- Cross-references con enlaces relativos (`[ver raw](../raw/fuente.md)`).
- Cada página debe tener al menos un párrafo de contexto antes de listas o tablas.
- Las páginas sin raw correspondiente son válidas (conocimiento sintetizado ad hoc).

### 2.3 `vault/config.md` — configuración de la instancia

Documento de configuración de este vault concreto. No es un README de uso general:
es la fuente de verdad de las convenciones adoptadas por este proyecto en particular.

**Contenido mínimo esperado**:
- Propósito del vault (en qué contexto se usa esta capa de conocimiento).
- Convenciones de nomenclatura de `raw/` y `wiki/` para este proyecto.
- Mapa de categorías o tags si se adoptan.
- Reglas de síntesis: qué convierte un raw en wiki (threshold de relevancia, etc.).

**Nota de naming**: el archivo se llama `config.md`, no `schema.md`, para evitar
confusión léxica con `questionnaire/schema.yaml` que es el schema del cuestionario
del generador.

## 3. Principios invariantes

Estos principios no pueden violarse al añadir adapters, renderers o herramientas
en fases posteriores (G2, G3, G4):

1. **File-based**: todo es Markdown plano. Sin base de datos, sin formato propietario,
   sin dependencia de un servidor. El vault puede leerse con cualquier editor de texto.

2. **Tool-agnostic**: ningún adapter es canónico. Obsidian + Web Clipper es el
   primer reference adapter previsto (G2), pero Logseq, Foam, Zettlr y plain-text
   son igualmente compatibles por construcción del contrato.

3. **Opt-in**: el questionnaire controla si el vault se emite. Un proyecto que no activa
   la capa no debe tener ningún directorio `vault/` ni referencia a él en sus templates.

4. **Sin runtime compartido**: el vault vive en el repo generado, no en el meta-repo.
   El generador emite el esqueleto; el mantenimiento es responsabilidad del proyecto destino.

5. **Sin ingest automático en G1**: la capa no implica ningún daemon, watcher ni
   llamada LLM automática. Ingest manual (G3) y lint (G4) son extensiones futuras opcionales.

## 4. Opt-in en el questionnaire

Campo: `integrations.knowledge_plane.enabled` (sección E, Integraciones).

```yaml
"integrations.knowledge_plane.enabled": true
```

Tipo: `boolean`. Default: `false`.

El generador evalúa este campo en G2 para ramificar la emisión del esqueleto `vault/`.
En G1 el campo es declarable y validable pero el renderer no existe todavía.

**Campos diferidos** (no en G1, regla #7 CLAUDE.md):
- `integrations.knowledge_plane.adapter` — diferido a G2+ cuando haya más de un adapter
  con semántica distinta.
- `integrations.knowledge_plane.vault_path` — diferido hasta que un caso real requiera
  un path personalizado (default sería `vault/`).

## 5. Scope de cada rama de Fase G

| Rama | Entrega | Depende de |
|---|---|---|
| G1 (esta rama) | Contrato + campo schema + regla path-scoped | — |
| G2 | Renderer Obsidian reference adapter, esqueleto `vault/` | G1 |
| G3 | Stub CLI `pos knowledge ingest` | G1 + G2 |
| G4 | Skill `/pos:knowledge-lint` | G1 + G2 + ≥2 proyectos reales |

## 6. Relación con el modelo de dos capas

El knowledge plane no altera el modelo de dos capas existente:

```
META-REPO (control plane)
    │ genera
    ▼
REPO GENERADO (runtime plane)
    │
    └── [opt-in] vault/    ← knowledge plane
```

El generador sólo emite el esqueleto. El control de contenido del vault
es local al proyecto destino y no depende del meta-repo en runtime.

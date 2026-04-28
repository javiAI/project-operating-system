import { describe, expect, it } from "vitest";
import { render } from "./knowledge-plane-vault.ts";
import type { Profile } from "../lib/profile-model.ts";

function makeProfileWithAnswers(answers: Record<string, unknown>): Profile {
  return {
    meta: { version: "1", profileName: "test", profileDescription: "test" },
    answers,
    placeholders: [],
  };
}

function makeProfile(enabled: unknown): Profile {
  return makeProfileWithAnswers(
    enabled === undefined ? {} : { integrations: { knowledge_plane: { enabled } } }
  );
}

const profileEnabled = makeProfile(true);
const profileDisabled = makeProfile(false);
const profileAbsent = makeProfile(undefined);
const profileIntegrationsNoKP = makeProfileWithAnswers({ integrations: {} });

describe("renderers/knowledge-plane-vault — opt-in gate", () => {
  it("returns [] when enabled is false", () => {
    expect(render(profileDisabled)).toEqual([]);
  });

  it("returns [] when enabled is absent (default false)", () => {
    expect(render(profileAbsent)).toEqual([]);
  });

  it("returns [] when integrations exists but knowledge_plane key is absent", () => {
    expect(render(profileIntegrationsNoKP)).toEqual([]);
  });

  it("returns exactly 3 FileWrite entries when enabled is true", () => {
    expect(render(profileEnabled)).toHaveLength(3);
  });
});

describe("renderers/knowledge-plane-vault — emitted paths", () => {
  it("emits vault/config.md", () => {
    const paths = render(profileEnabled).map((f) => f.path);
    expect(paths).toContain("vault/config.md");
  });

  it("emits vault/raw/.gitkeep", () => {
    const paths = render(profileEnabled).map((f) => f.path);
    expect(paths).toContain("vault/raw/.gitkeep");
  });

  it("emits vault/wiki/.gitkeep", () => {
    const paths = render(profileEnabled).map((f) => f.path);
    expect(paths).toContain("vault/wiki/.gitkeep");
  });

  it("does NOT emit vault/schema.md (naming: config.md wins per G1 rule)", () => {
    const paths = render(profileEnabled).map((f) => f.path);
    expect(paths).not.toContain("vault/schema.md");
  });
});

describe("renderers/knowledge-plane-vault — .gitkeep content", () => {
  it("vault/raw/.gitkeep has empty content (single newline)", () => {
    const file = render(profileEnabled).find((f) => f.path === "vault/raw/.gitkeep")!;
    expect(file.content).toBe("\n");
  });

  it("vault/wiki/.gitkeep has empty content (single newline)", () => {
    const file = render(profileEnabled).find((f) => f.path === "vault/wiki/.gitkeep")!;
    expect(file.content).toBe("\n");
  });
});

describe("renderers/knowledge-plane-vault — vault/config.md content", () => {
  it("contains ## Propósito section", () => {
    const file = render(profileEnabled).find((f) => f.path === "vault/config.md")!;
    expect(file.content).toMatch(/^## Propósito/m);
  });

  it("contains ## Estructura section", () => {
    const file = render(profileEnabled).find((f) => f.path === "vault/config.md")!;
    expect(file.content).toMatch(/^## Estructura/m);
  });

  it("contains ## Convenciones raw section", () => {
    const file = render(profileEnabled).find((f) => f.path === "vault/config.md")!;
    expect(file.content).toMatch(/^## Convenciones raw/m);
  });

  it("contains ## Convenciones wiki section", () => {
    const file = render(profileEnabled).find((f) => f.path === "vault/config.md")!;
    expect(file.content).toMatch(/^## Convenciones wiki/m);
  });

  it("contains ## Ingestor recomendado section", () => {
    const file = render(profileEnabled).find((f) => f.path === "vault/config.md")!;
    expect(file.content).toMatch(/^## Ingestor recomendado/m);
  });

  it("mentions Obsidian Web Clipper as reference ingestor", () => {
    const file = render(profileEnabled).find((f) => f.path === "vault/config.md")!;
    expect(file.content).toMatch(/Obsidian Web Clipper/i);
  });

  it("explicitly states the adapter is a reference, not a base contract", () => {
    const file = render(profileEnabled).find((f) => f.path === "vault/config.md")!;
    expect(file.content).toMatch(/referencia|reference/i);
  });
});

describe("renderers/knowledge-plane-vault — structural invariants", () => {
  it("every emitted file ends with a trailing newline", () => {
    for (const f of render(profileEnabled)) {
      expect(f.content.endsWith("\n"), `${f.path} must end with \\n`).toBe(true);
    }
  });

  it("is deterministic: byte-identical FileWrite[] across runs", () => {
    expect(JSON.stringify(render(profileEnabled))).toBe(
      JSON.stringify(render(profileEnabled))
    );
  });
});

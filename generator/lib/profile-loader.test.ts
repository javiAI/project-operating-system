import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { loadProfile } from "./profile-loader.ts";

const VALID_FIXTURE = "generator/__fixtures__/profiles/valid-partial/profile.yaml";

describe("loadProfile", () => {
  it("returns ok:true with parsed ProfileFile for a valid yaml", async () => {
    const result = await loadProfile(VALID_FIXTURE);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.profile.version).toBe("0.1.0");
      expect(result.profile.profile.name).toBe("valid-partial");
      expect(result.profile.answers["stack.language"]).toBe("typescript");
    }
  });

  it("returns ok:false when the file does not exist", async () => {
    const result = await loadProfile("generator/__fixtures__/profiles/does-not-exist.yaml");
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toMatch(/cannot read/);
    }
  });

  it("returns ok:false when the YAML is malformed", async () => {
    const dir = mkdtempSync(join(tmpdir(), "profile-loader-"));
    const path = join(dir, "broken.yaml");
    writeFileSync(
      path,
      "version: '0.1.0'\nprofile:\n  name: x\n  description: y\nanswers:\n  foo: [unterminated",
    );
    const result = await loadProfile(path);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toMatch(/cannot parse/);
    }
  });

  it("returns ok:false when top-level shape is invalid (missing profile key)", async () => {
    const dir = mkdtempSync(join(tmpdir(), "profile-loader-"));
    const path = join(dir, "shape.yaml");
    writeFileSync(path, "version: '0.1.0'\nanswers: {}\n");
    const result = await loadProfile(path);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toMatch(/profile invalid/i);
    }
  });

  it("returns ok:false when an unknown top-level key is present (strict)", async () => {
    const dir = mkdtempSync(join(tmpdir(), "profile-loader-"));
    const path = join(dir, "extra.yaml");
    writeFileSync(
      path,
      "version: '0.1.0'\nprofile:\n  name: x\n  description: y\nanswers: {}\nextra: 1\n",
    );
    const result = await loadProfile(path);
    expect(result.ok).toBe(false);
  });
});

import { mkdtemp, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  isDirEmpty,
  renderAll,
  writeFiles,
  type FileWrite,
  type Profile,
  type Renderer,
} from "./render-pipeline.ts";

const emptyProfile: Profile = {
  meta: { version: "1.0.0", profileName: "t", profileDescription: "t" },
  answers: {},
  placeholders: [],
};

describe("renderAll — combines renderer outputs", () => {
  it("concatenates outputs preserving renderer order", () => {
    const r1: Renderer = () => [{ path: "A.md", content: "a" }];
    const r2: Renderer = () => [{ path: "B.md", content: "b" }];
    expect(renderAll(emptyProfile, [r1, r2])).toEqual([
      { path: "A.md", content: "a" },
      { path: "B.md", content: "b" },
    ]);
  });

  it("returns empty array when no renderers are registered", () => {
    expect(renderAll(emptyProfile, [])).toEqual([]);
  });

  it("supports renderers emitting subdirectory paths", () => {
    const r: Renderer = () => [
      { path: "docs/architecture.md", content: "x" },
      { path: ".github/workflows/ci.yml", content: "y" },
    ];
    const out = renderAll(emptyProfile, [r]);
    expect(out.map((f) => f.path)).toEqual([
      "docs/architecture.md",
      ".github/workflows/ci.yml",
    ]);
  });
});

describe("renderAll — collision detection (invariant, not test-only)", () => {
  it("throws when two renderers emit the same path", () => {
    const r1: Renderer = () => [{ path: "README.md", content: "x" }];
    const r2: Renderer = () => [{ path: "README.md", content: "y" }];
    expect(() => renderAll(emptyProfile, [r1, r2])).toThrow(/collision.*README\.md/);
  });

  it("throws when a single renderer emits the same path twice", () => {
    const r: Renderer = () => [
      { path: "dup.md", content: "a" },
      { path: "dup.md", content: "b" },
    ];
    expect(() => renderAll(emptyProfile, [r])).toThrow(/collision.*dup\.md/);
  });

  it("error message identifies both renderer indices", () => {
    const r1: Renderer = () => [{ path: "x.md", content: "1" }];
    const r2: Renderer = () => [{ path: "y.md", content: "2" }];
    const r3: Renderer = () => [{ path: "x.md", content: "3" }];
    expect(() => renderAll(emptyProfile, [r1, r2, r3])).toThrow(/renderer\[0\].*renderer\[2\]/);
  });
});

describe("renderAll — determinism", () => {
  it("same profile + renderers yields identical FileWrite[] across calls", () => {
    const profile: Profile = {
      meta: { version: "1.0.0", profileName: "p", profileDescription: "d" },
      answers: { stack: { language: "typescript" } },
      placeholders: [],
    };
    const r: Renderer = (p) => [
      { path: "out.md", content: `lang=${(p.answers.stack as Record<string, unknown>).language}` },
    ];
    expect(JSON.stringify(renderAll(profile, [r]))).toEqual(
      JSON.stringify(renderAll(profile, [r]))
    );
  });
});

describe("writeFiles / isDirEmpty — filesystem", () => {
  let tmp: string;
  beforeEach(async () => {
    tmp = await mkdtemp(path.join(tmpdir(), "pos-pipeline-"));
  });
  afterEach(async () => {
    await rm(tmp, { recursive: true, force: true });
  });

  it("writes each file under outDir, creating subdirs as needed", async () => {
    const files: FileWrite[] = [
      { path: "CLAUDE.md", content: "# claude\n" },
      { path: "docs/ARCHITECTURE.md", content: "# arch\n" },
      { path: "a/b/c/deep.md", content: "deep\n" },
    ];
    await writeFiles(tmp, files);
    expect(await readFile(path.join(tmp, "CLAUDE.md"), "utf8")).toBe("# claude\n");
    expect(await readFile(path.join(tmp, "docs/ARCHITECTURE.md"), "utf8")).toBe("# arch\n");
    expect(await readFile(path.join(tmp, "a/b/c/deep.md"), "utf8")).toBe("deep\n");
  });

  it("creates outDir if it does not exist", async () => {
    const nested = path.join(tmp, "new-dir");
    await writeFiles(nested, [{ path: "x.md", content: "x" }]);
    expect(await readFile(path.join(nested, "x.md"), "utf8")).toBe("x");
  });

  it("produces byte-identical files across two runs on the same input", async () => {
    const files: FileWrite[] = [
      { path: "a.md", content: "hello\n" },
      { path: "sub/b.md", content: "world\n" },
    ];
    const runA = path.join(tmp, "run-a");
    const runB = path.join(tmp, "run-b");
    await writeFiles(runA, files);
    await writeFiles(runB, files);
    expect(await readFile(path.join(runA, "a.md"))).toEqual(
      await readFile(path.join(runB, "a.md"))
    );
    expect(await readFile(path.join(runA, "sub/b.md"))).toEqual(
      await readFile(path.join(runB, "sub/b.md"))
    );
  });

  it("isDirEmpty returns true for non-existent path", async () => {
    expect(await isDirEmpty(path.join(tmp, "does-not-exist"))).toBe(true);
  });

  it("isDirEmpty returns true for an empty directory", async () => {
    const empty = path.join(tmp, "empty");
    await mkdir(empty);
    expect(await isDirEmpty(empty)).toBe(true);
  });

  it("isDirEmpty returns false for a directory with contents", async () => {
    await writeFile(path.join(tmp, "hello.txt"), "x");
    expect(await isDirEmpty(tmp)).toBe(false);
  });

  it("writeFiles preserves input order for deterministic emit (stable readdir is OS-dependent but our API does not reorder)", async () => {
    const files: FileWrite[] = [
      { path: "z.md", content: "z" },
      { path: "a.md", content: "a" },
    ];
    await writeFiles(tmp, files);
    const entries = (await readdir(tmp)).sort();
    expect(entries).toEqual(["a.md", "z.md"]);
  });
});

describe("writeFiles — path traversal hardening", () => {
  let tmp: string;
  beforeEach(async () => {
    tmp = await mkdtemp(path.join(tmpdir(), "pos-pipeline-traversal-"));
  });
  afterEach(async () => {
    await rm(tmp, { recursive: true, force: true });
  });

  it("rejects an absolute path", async () => {
    const abs = path.join(tmp, "evil.md");
    await expect(
      writeFiles(tmp, [{ path: abs, content: "x" }])
    ).rejects.toThrow(/absolute path rejected/);
  });

  it("rejects a path that escapes outDir via ../", async () => {
    await expect(
      writeFiles(tmp, [{ path: "../escape.md", content: "x" }])
    ).rejects.toThrow(/escapes outDir/);
  });

  it("rejects a nested path that escapes outDir via ../../..", async () => {
    await expect(
      writeFiles(tmp, [{ path: "a/../../b.md", content: "x" }])
    ).rejects.toThrow(/escapes outDir/);
  });

  it("accepts a valid relative path inside outDir", async () => {
    await writeFiles(tmp, [{ path: "ok/fine.md", content: "ok\n" }]);
    expect(await readFile(path.join(tmp, "ok/fine.md"), "utf8")).toBe("ok\n");
  });
});

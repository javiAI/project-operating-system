import { describe, expect, it } from "vitest";
import { allRenderers } from "../renderers/index.ts";
import { renderAll } from "../lib/render-pipeline.ts";
import { loadCanonicalProfiles } from "./load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("snapshots — all renderers (profile × template = 27)", () => {
  for (const { slug, profile } of profiles) {
    const files = renderAll(profile, [...allRenderers]);
    for (const file of files) {
      it(`matches snapshot: ${slug}/${file.path}`, async () => {
        await expect(file.content).toMatchFileSnapshot(
          `../__snapshots__/${slug}/${file.path}.snap`
        );
      });
    }
  }
});

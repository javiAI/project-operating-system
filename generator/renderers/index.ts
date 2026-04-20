import type { Renderer } from "../lib/render-pipeline.ts";
import { render as renderClaudeMd } from "./claude-md.ts";
import { render as renderMasterPlan } from "./master-plan.ts";
import { render as renderRoadmap } from "./roadmap.ts";
import { render as renderHandoff } from "./handoff.ts";
import { render as renderAgents } from "./agents.ts";
import { render as renderReadme } from "./readme.ts";

export const coreDocRenderers: readonly Renderer[] = Object.freeze([
  renderClaudeMd,
  renderMasterPlan,
  renderRoadmap,
  renderHandoff,
  renderAgents,
  renderReadme,
]);

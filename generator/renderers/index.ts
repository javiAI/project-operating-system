import type { Renderer } from "../lib/render-pipeline.ts";
import { render as renderClaudeMd } from "./claude-md.ts";
import { render as renderMasterPlan } from "./master-plan.ts";
import { render as renderRoadmap } from "./roadmap.ts";
import { render as renderHandoff } from "./handoff.ts";
import { render as renderAgents } from "./agents.ts";
import { render as renderReadme } from "./readme.ts";
import { render as renderPolicy } from "./policy.ts";
import { render as renderRules } from "./rules.ts";
import { render as renderTests } from "./tests.ts";
import { render as renderCiCd } from "./ci-cd.ts";
import { render as renderSkillsHooksSkeleton } from "./skills-hooks-skeleton.ts";

export const coreDocRenderers: readonly Renderer[] = Object.freeze([
  renderClaudeMd,
  renderMasterPlan,
  renderRoadmap,
  renderHandoff,
  renderAgents,
  renderReadme,
]);

export const policyAndRulesRenderers: readonly Renderer[] = Object.freeze([
  renderPolicy,
  renderRules,
]);

export const testsHarnessRenderers: readonly Renderer[] = Object.freeze([
  renderTests,
]);

export const cicdRenderers: readonly Renderer[] = Object.freeze([
  renderCiCd,
]);

export const skillsHooksRenderers: readonly Renderer[] = Object.freeze([
  renderSkillsHooksSkeleton,
]);

export const allRenderers: readonly Renderer[] = Object.freeze([
  ...coreDocRenderers,
  ...policyAndRulesRenderers,
  ...testsHarnessRenderers,
  ...cicdRenderers,
  ...skillsHooksRenderers,
]);

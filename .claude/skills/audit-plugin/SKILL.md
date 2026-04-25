---
name: audit-plugin
description: Use when about to install a community tool (MCP, plugin, package) that is not from Anthropic or an explicitly trusted source. Audits against docs/SAFETY_POLICY.md and returns GO / NO-GO / NEEDS_MORE_INFO. Advisory-only; does not enforce or block installation.
allowed-tools:
  - Read
  - Bash(cd:., find:., curl:--head-only, grep:.)
---

## Framing

This skill gates third-party tools *before* installation. It's advisory: you get a decision (`GO / NO-GO / NEEDS_MORE_INFO`) and the reasoning. You decide whether to install, escalate, or wait.

**Important**: E2b delivers advisory-only evaluation. Hard enforcement (blocking `npm install`, managing `approved_overrides`, audit logs) is deferred to a future branch.

## Scope (strict)

You MAY:
- Read `docs/SAFETY_POLICY.md` (the checklist your audit follows).
- Read tool manifest (e.g., `package.json`, `plugin.json`, repo README).
- Inspect declared source / homepage / license / version.
- Check tool against `policy.yaml.safety` trusted sources + denylist.
- Ask the user for clarification (e.g., "what does this tool do?", "can you share the source URL?").

You MUST NOT:
- Install, fetch, or execute the tool.
- Modify `policy.yaml` or add overrides.
- Create `.claude/logs/audits/` or any log files.
- Enforce or block installation (no hook integration yet).
- Access private repos or credentials.
- Download and scan tool source code without user consent.

## Steps

1. **Gather tool info** — ask user for: tool name, package URL/repo, version, intended use.

2. **Check denylist** — is the tool in `policy.yaml.safety.community_tool_gate.denylist`? If YES → **NO-GO** immediately, cite reason from SAFETY_POLICY.md.

3. **Check trusted sources** — is it in `anthropic-mcp-registry`, `@anthropics/*`, or `javiAI/*`? If YES → **GO** (pre-trusted).

4. **Check optin starter list** — is it `mempalace` or `notebooklm-mcp`? If YES → **GO** (pre-audited).

5. **Run SAFETY_POLICY.md checklist**:
   - [ ] Manifest review (license, version pin, homepage accessible)
   - [ ] Hooks inspection (no unsafe patterns: `eval`, `curl` in hooks, etc.)
   - [ ] MCP server inspection (declared args, no hardcoded creds, scope explicit)
   - [ ] Permissions (allowed-tools minimal, no overpermitting)
   - [ ] Runtime footprint (dependencies audited, no post-install network calls)
   - [ ] Versioning + pin (version exact, not `latest` or range)

   If checklist incomplete or tool source unavailable → **NEEDS_MORE_INFO** ("Please share the source repo so we can inspect it").

6. **Decision**:
   - All items ✓ → **GO**
   - Any item ✗ → **NO-GO** (cite which items failed)
   - Blocked due to missing info → **NEEDS_MORE_INFO**

7. **Output format**:
   ```markdown
   ## Audit result: [GO | NO-GO | NEEDS_MORE_INFO]

   **Tool**: <name> <version>
   **Source**: <repo/package URL>

   ### Checklist

   | Item | Status | Notes |
   |------|--------|-------|
   | License check | ✓ | MIT, acceptable |
   | Version pinned | ✗ | Using `latest`, should pin |
   | ...

   ### Recommendation

   - If GO: "Safe to install. No known security concerns."
   - If NO-GO: "Do not install without fixes. Blocker: [specific reason]."
   - If NEEDS_MORE_INFO: "Cannot audit yet. Please provide: [what's missing]."

   ---

   **Note**: This audit is advisory-only in E2b. Hard enforcement and logged audit trails come in a future branch.
   ```

8. **Stop** — do NOT install or modify policy. User decides next step.

9. **Log invocation** (best-effort):
   ```bash
   .claude/skills/_shared/log-invocation.sh audit-plugin ok
   ```

## Explicitly out of scope (E2b)

- Enforcing or blocking installation.
- Creating `.claude/logs/audits/<tool>-<version>.md`.
- Managing `policy.yaml.safety.community_tool_gate.approved_overrides`.
- Hook integration with `npm install`.
- Re-audit scheduling or CVE monitoring.
- Appeal process workflows.

## Failure modes

- User cannot share tool source (closed/private repo) → NEEDS_MORE_INFO + suggest opening issue with maintainer.
- Denylist / trusted sources unavailable in `policy.yaml` → proceed with manual checklist (policy availability not guaranteed).
- Checklist ambiguous (e.g., "no eval" unclear in tool source) → surface the specific check that's ambiguous and ask user for clarification.

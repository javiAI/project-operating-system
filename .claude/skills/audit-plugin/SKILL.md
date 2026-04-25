---
name: audit-plugin
description: Use when about to install a community tool (MCP, plugin, package) that is not from Anthropic or an explicitly trusted source. Audits against docs/SAFETY_POLICY.md and returns GO / NO-GO / NEEDS_MORE_INFO. Advisory-only; does not enforce, modify policy, or block installation.
allowed-tools:
  - Read
  - Bash(grep:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

## Framing

This skill gates third-party tools *before* installation. It's **read-only advisory**: you receive a decision (`GO / NO-GO / NEEDS_MORE_INFO`) + reasoning. You decide whether to install, escalate, or wait.

**Important scope clarification (E2b)**: This skill is advisory-only. Hard enforcement (blocking `npm install`, managing `approved_overrides`, creating audit logs, modifying `policy.yaml`) is deferred to a future branch.

## Scope (strict)

You MAY:
- Read `docs/SAFETY_POLICY.md` (your checklist source).
- Read tool manifest (e.g., `package.json`, `skill.md` frontmatter, README).
- Inspect declared source / homepage / license / version.
- Cross-check against `policy.yaml.safety.community_tool_gate` trusted sources + denylist.
- Ask the user for clarification or missing information.

You MUST NOT:
- Install, execute, or download the tool.
- Modify `policy.yaml` or create `approved_overrides`.
- Create `.claude/logs/audits/` or any log files.
- Enforce or block installation (advisory-only in E2b; enforcement deferred).
- Access private repos, credentials, or network resources without user consent.

## Steps

1. **Gather info** — ask user for: tool name, package/repo URL, version, intended use case.

2. **Check denylist** — search `policy.yaml.safety.community_tool_gate.denylist` and `docs/SAFETY_POLICY.md` denylist. If found → **NO-GO** + cite reason.

3. **Check trusted sources** — is it from `anthropic-mcp-registry`, `@anthropics/*`, or `github.com/javiAI/*`? If yes → **GO** (pre-trusted).

4. **Check optin starter list** — is it `mempalace` or `notebooklm-mcp`? If yes → **GO** (pre-audited).

5. **Run SAFETY_POLICY.md checklist** (6 items):
   - Manifest review: license, version pin, homepage accessible?
   - Hooks inspection: no `eval`, `exec`, `curl` in shell commands?
   - MCP server: declared args, no hardcoded credentials?
   - Permissions: `allowed-tools` minimal, no overpermitting?
   - Runtime footprint: dependencies audited, no post-install network calls?
   - Versioning: version exact (not `latest` or range)?

6. **Decide**:
   - All checks ✓ → **GO**
   - Any check ✗ → **NO-GO** (which items failed?)
   - Missing tool source or manifest → **NEEDS_MORE_INFO**

7. **Output**:
   ```markdown
   ## Audit result: [GO | NO-GO | NEEDS_MORE_INFO]

   **Tool**: <name> <version>
   **Source**: <URL>

   ### Checklist

   | Item | Status | Note |
   |------|--------|------|
   | Manifest review | ✓ | MIT, v1.2.3 pinned |
   | Hooks inspection | ✗ | Uses `eval` without sanitization |
   | ...

   ### Recommendation

   - **GO**: Safe to install. No security concerns found.
   - **NO-GO**: Do not install. Blocker(s): [list].
   - **NEEDS_MORE_INFO**: Cannot audit. Please provide: [what's needed].

   ---

   **Note**: E2b advisory-only. Enforcement + audit logging deferred.
   ```

8. **STOP** — do NOT install or modify policy. User decides.

9. **Log invocation** (best-effort):
   ```bash
   .claude/skills/_shared/log-invocation.sh audit-plugin ok
   ```

## Explicitly out of scope (E2b)

- Enforcing or blocking installation.
- Creating audit logs in `.claude/logs/audits/`.
- Modifying `policy.yaml`.
- Hook integration with `npm install`.
- Re-audit scheduling or CVE monitoring.
- Appeal workflows.

## Failure modes

- Denylist unavailable → proceed with manual checklist.
- Tool source closed/private → NEEDS_MORE_INFO + suggest opening maintainer issue.
- Checklist ambiguous (e.g., "no eval" ambiguous in source) → ask user to clarify.

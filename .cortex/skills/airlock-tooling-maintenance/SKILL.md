---
name: airlock-tooling-maintenance
description: Identify Airlock stored procedure, documentation, workflow, schema, or safety-contract changes that require updates to the Airlock MCP server, Cortex Code skill, docs, tests, or Snowflake CLI usage guidance.
tools:
- snowflake_sql_execute
- snowflake_object_search
---

# When to Use

Use this skill when asked whether Airlock changes require updates to this
repository, the Airlock MCP server, the Airlock Cortex Code skill, public docs,
tests, or Snowflake CLI runbooks.

# Core Rule

Installed Airlock documentation and procedure results are the source of truth.
Do not infer compatibility from repo docs alone. Compare the installed Airlock
API against this repo's MCP tools, CoCo skills, docs, examples, and tests.
Use the public Airlock docs site and spec library as supporting context, not as
the authoritative installed procedure contract:

- `https://reunionstudio.io/airlock/docs/index.html`
- `https://reunionstudio.io/airlock/docs/spec-library.html`

# Drift Signals

An Airlock change needs review here when any of these change:

- `airlock.user.documentation()` `content_hash` or `etag`.
- `CONTENT_MODE => 'PROCEDURES'` procedure names, signatures, arguments, or
  section ids.
- Procedure return columns, `STATUS`, `CODE`, `MESSAGE`, `ISSUES`,
  `VALIDATION`, `PAYLOAD`, or row shape.
- User/admin boundary, application role grants, Airlock role lens behavior, or
  license-seat behavior.
- Spec descriptor fields: `column_config`, `file_rules`, `attachment_policy`,
  `file_workflow`, `accessible_paths`, references, expectations, or path scopes.
- Safety semantics: `validate_only`, `dry_run`, `force`, confirmation,
  destructive behavior, attachment replace/delete permanence, workflow
  reversibility.
- New user workflows that should become MCP tools, resources, prompts, skill
  examples, or tests.
- Delegation procedures, `on_behalf_of_user` / `delegation_id` parameters,
  actor/principal/delegation result fields, or delegation denial codes.
- Snowflake connection requirements, authentication guidance, CLI syntax, or
  installation mechanics.
- Public documentation or spec-library guidance that changes recommended agent
  workflows, spec modeling patterns, or examples in this repo.
- Marketplace listing, Native App privilege, install, uninstall, ownership
  transfer, or `AIRLOCK_DATA` storage/reinstall guidance.
- Architecture playbook or product philosophy changes that affect MCP prompts,
  skill references, public docs, or examples.

# Required Check

1. Capture the active Snowflake context and Airlock docs from the installed app:
   ```sql
   SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_WAREHOUSE();
   CALL airlock.user.documentation();
   CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');
   CALL airlock.user.documentation(CONTENT_MODE => 'SECTION', SECTION_IDS => 'guidance-for-ai-agents-and-automation');
   CALL airlock.user.list_my_roles();
   ```
2. If admin access is available and the task concerns admin behavior, also run:
   ```sql
   CALL airlock.admin.api_info();
   ```
3. Compare installed procedures to:
   - `src/airlock_mcp/server.py` MCP tools/resources/prompts.
   - `.cortex/skills/airlock/SKILL.md` and examples.
   - `.cortex/skills/airlock-tooling-maintenance/` references.
   - `README.md` and `docs/*.md`.
   - `tests/`.
   - Public Airlock docs and spec-library guidance when the task concerns
     product concepts, examples, or spec design.
   - Airlock Marketplace listing and Snowflake Native App docs when the task
     concerns install, privileges, uninstall, data retention, or reinstall.
   - `.cortex/skills/airlock/references/architecture-playbook.md` when the task
     concerns architecture philosophy or product context.
4. Classify each difference:
   - No action: additive change outside this repo's supported surface.
   - Docs only: wording/examples/runbook update.
   - Skill update: CoCo behavior or examples must change.
   - MCP update: tool signature, safety gate, return normalization, resource, or
     prompt must change.
   - Test update: fixture, mapping, safety gate, or integration case must change.
   - Breaking risk: existing tool behavior may call the wrong procedure or hide
     important structured output.
5. Preserve Airlock reason codes and structured outputs in any update.

# Snowflake CLI

If local SQL access is needed, read
`references/snowflake-cli-airlock.md` for setup and command examples. Prefer
Snowflake CLI `snow sql` for quick installed-doc snapshots when MCP is not yet
configured.

# Update Rules

- Prefer adding narrow tests before changing tool behavior.
- Do not add direct queries against Airlock-owned tables, stages, or secure
  views.
- Keep admin tools disabled by default unless product policy changes.
- Keep destructive MCP tools defaulting to preview or requiring explicit
  confirmation.
- Keep MCP delegation tools aligned with installed Airlock documentation.
- Preserve actor user, principal user, delegation id, and denial codes in MCP
  output.
- Update the normal Airlock CoCo skill when workflow guidance changes.
- Update `README.md` and docs when setup, packaging, or compatibility changes.
- Update `.cortex/skills/airlock/references/marketplace-install-and-security.md`
  when Marketplace install, Native App security, app permissions, uninstall, or
  `AIRLOCK_DATA` guidance changes.
- Update `.cortex/skills/airlock/references/architecture-playbook.md` and MCP
  architecture prompts when the Airlock thesis, examples, or product context
  changes.
- Record what installed Airlock version/hash was reviewed.

# Output

Report findings first:

- `P0`: current MCP/skill behavior is unsafe or calls the wrong procedure.
- `P1`: supported workflow is broken or missing required arguments/output.
- `P2`: docs, examples, tests, or prompt guidance are stale.
- `P3`: optional enhancement or future tool opportunity.

For each finding, name the installed procedure, the repo file that must change,
and the exact reason.

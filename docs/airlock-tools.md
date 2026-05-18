# Airlock Tools for AI Agents

This guide combines the Airlock MCP server guidance and the Airlock AI-agent
skill guidance into one neutral reference. It applies to Codex, Claude,
OpenClaw, Snowflake-hosted agents, MCP clients, and future AI assistants.

The goal is simple: make Airlock easy for agents to use while keeping Airlock's
Snowflake stored procedures as the source of truth for permissions, validation,
audit, retention, billing, and workflow.

## Positioning

Airlock is a policy-enforcing ingestion layer. Agents and MCP servers should use
documented Airlock stored procedures. They should not write directly to
Airlock-owned stages, hybrid tables, secure views, or generated replacement
apps.

An Airlock MCP server or agent skill is an adapter and teaching layer:

- the agent discovers the installed Airlock API
- the tool or skill maps user intent to documented procedure calls
- Snowflake grants, application roles, Airlock roles, licenses, and the Airlock
  PDP enforce authorization
- procedure results remain structured and auditable

The adapter must not reimplement Airlock business logic outside Snowflake.

## Core Concepts

Always distinguish:

- **Snowflake role**: controls access to the app object and procedure grants.
- **Snowflake application role**: `app_user` or `app_admin`.
- **Airlock role**: business role stored inside Airlock, used for granular spec,
  path, workflow, and admin scope.
- **Delegation**: user-to-agent authority for stored procedure calls. Delegation
  is not an Airlock role and is not a Streamlit identity mode.

When a caller has multiple Airlock roles, pass the intended `in_app_role` lens to
procedures that accept it. Do not mix Airlock roles with Snowflake roles in tool
names, descriptions, or error messages.

## MCP and Stored Procedures

MCP is a structured way for AI clients to discover and call external
capabilities through tools, resources, and optional prompts. Airlock is not an
MCP server by itself; it is a database-native API exposed through Snowflake
stored procedures.

The mapping is direct:

| MCP idea | Airlock analogue |
| --- | --- |
| Tool name | `airlock.user.*`, `airlock.admin.*`, `airlock.billing.*` procedures |
| Tool description | `airlock.user.documentation(...)`, `airlock.user.help(...)`, `airlock.admin.help(...)`, `airlock.billing.help(...)` |
| Catalog / discovery | `airlock.admin.api_info()` and installed documentation |
| Invocation | `CALL airlock.user.load_data(...)` and related procedure calls |
| Authorization | Snowflake grants, application roles, Airlock roles, licenses, and PDP checks |

An MCP server can make Airlock easier for agents by wrapping procedures with
typed tools and JSON Schema. It should remain a thin, auditable transport layer.

Recommended MCP shape:

```text
MCP client
  -> Airlock MCP server
      -> Snowflake connector or Snowflake CLI-compatible connection
          -> CALL airlock.user.* / airlock.admin.*
              -> Airlock procedures, PDP, events, owned storage
```

The server may be Python, Node, or another runtime. Each tool should map to one
documented Airlock operation or a small transparent sequence of documented
operations.

## Agent Skill Shape

An Airlock skill teaches an agent the workflow and safety model. It may be
packaged for any agent ecosystem: repo-local skills, user-local skills, hosted
agent instructions, shared Git repositories, or Snowflake stage distribution.

Recommended generic layout:

```text
airlock-agent-tools/
  airlock/
    SKILL.md
    examples/
      submit-file-with-attachment.md
      draft-spec-from-template.md
    templates/
      spec-config-minimal.json
  README.md
```

Project-local variants may use whatever the host expects, such as:

```text
.codex/skills/airlock/
.claude/skills/airlock/
.cortex/skills/airlock/
.agents/skills/airlock/
```

Adjust tool names to the host. If an Airlock MCP server exists, the skill should
prefer typed Airlock tools. Without MCP, it should call SQL procedures directly.

## Minimal Skill

```markdown
---
name: airlock
description: Use Airlock stored procedures for governed spec discovery, validation, file loading, workflow, attachments, delegations, and safe admin operations.
tools:
- snowflake_sql_execute
- snowflake_object_search
---

# When to Use

Use this skill when the user asks an AI agent to work with Airlock, submit data,
create or inspect specs, validate files, attach evidence, move workflow, inspect
expectations, create delegations, or automate governed ingestion into Snowflake.

# Core Rule

Airlock is the policy-enforcing ingestion layer. Do not write directly to
Airlock-owned stages, hybrid tables, secure views, or generated replacement
apps. Use installed Airlock stored procedures and preserve structured outputs.

# First Steps

1. Confirm the active Snowflake connection and role.
2. Query installed Airlock documentation:
   `CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');`
3. List the caller's Airlock roles:
   `CALL airlock.user.list_my_roles();`
4. Use `airlock.user.list_my_specs(in_app_role)` and
   `airlock.user.describe_spec(spec_name, in_app_role)` before choosing any
   load, validate, attachment, workflow, or reference call.

# Safe Procedure Pattern

For data submission:

1. Describe the spec.
2. Build CSV or file content that matches `column_config` and `file_rules`.
3. Call `airlock.user.validate_data(...)`.
4. Only if validation succeeds, call `airlock.user.load_data(...)`.
5. If the spec requires attachments, include `attachment_content_base64` and
   `attachment_filename` in `load_data`, or use `add_attachment` afterward when
   the policy allows it.
6. Report `STATUS`, `CODE`, `MESSAGE`, `ISSUES`, returned path, filename, and
   workflow state.

# Safety

- Ask before mutating admin configuration.
- Use `validate_only` for declarative create/alter APIs when available.
- Use `dry_run` for destructive operational previews when available.
- Do not hide Airlock reason codes.
- Do not suggest broad Snowflake privileges when an Airlock role, license,
  template, delegation, or workflow fix is the actual issue.
- Treat attachment replace/delete as permanent in Airlock unless installed docs
  say a tested restore path exists.
```

## Discovery First

Installed documentation beats repo docs. Agents should start with:

```sql
CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');
CALL airlock.user.list_my_roles();
CALL airlock.user.list_my_specs('<airlock_role>');
CALL airlock.user.describe_spec('<spec_name>', '<airlock_role>');
```

For admin work:

```sql
CALL airlock.admin.api_info();
CALL airlock.admin.list_specs('<airlock_role>');
CALL airlock.admin.describe_spec('<spec_name>');
```

Agents should preserve help output and procedure result payloads instead of
turning everything into prose.

## Recommended MCP Tool Surface

Use names that describe Airlock concepts and map clearly to procedures. Start
with user-safe tools, then add admin tools behind explicit configuration.

### Discovery Tools

| Tool | Maps to | Purpose |
| --- | --- | --- |
| `airlock_get_api_info` | `airlock.admin.api_info()` when admin; docs fallback via `documentation()` | Discover installed API version and procedure availability. |
| `airlock_get_documentation` | `airlock.user.documentation(...)` | Fetch TOC, procedure registry, sections, chunks, or full docs. |
| `airlock_list_my_roles` | `airlock.user.list_my_roles()` | Identify caller's Airlock roles. |
| `airlock_check_license` | `airlock.user.get_my_license_seat()` / `airlock.user.claim_license_seat()` when claim is approved | Tell agents whether user APIs can run. |
| `airlock_create_delegation` | `airlock.user.create_delegation(delegation_descriptor, validate_only)` | Let the current user grant their own agent scoped access to a spec they can write to. |
| `airlock_list_my_delegations` | `airlock.user.list_my_delegations(direction, spec_name, include_inactive)` | List delegations involving the caller; `received` is the agent action lens, `granted` is the principal audit lens. |

### Spec and Reference Tools

| Tool | Maps to | Purpose |
| --- | --- | --- |
| `airlock_list_specs` | `airlock.user.list_my_specs(in_app_role)` | List specs accessible to the caller. |
| `airlock_describe_spec` | `airlock.user.describe_spec(spec_name, in_app_role)` | Return fields, tests, file rules, workflow, attachments, path scopes, and reference guidance. |
| `airlock_select_reference_data` | `airlock.user.select_reference_data(...)` | Read approved reference-spec data for validation/planning. |

### File and Data Tools

| Tool | Maps to | Purpose |
| --- | --- | --- |
| `airlock_validate_data` | `airlock.user.validate_data(...)` | Validate candidate file content without writing. |
| `airlock_load_data` | `airlock.user.load_data(...)` | Load data into a spec/path; supports inline CSV or staged file path. |
| `airlock_list_files` | `airlock.user.list_my_files(spec_name, ...)` | Discover active/history files the caller may see. |
| `airlock_select_files` | `airlock.user.select_my_files(spec_name, ...)` | Read file data through Airlock access checks. |
| `airlock_delete_files` | `airlock.user.delete_files(..., dry_run)` | Preview or perform file delete where allowed. |

For destructive operations, require explicit confirmation or `dry_run=false`, and
preserve Airlock's own dry-run output.

### Workflow Tools

| Tool | Maps to | Purpose |
| --- | --- | --- |
| `airlock_list_work_items` | `airlock.user.list_my_work_items(...)` | List files that can be moved through workflow. |
| `airlock_edit_file_workflow` | `airlock.user.edit_file_workflow(...)` | Move a file to an allowed workflow state. |
| `airlock_list_file_references` | `airlock.user.list_file_references(...)` | Inspect source-link pins between files. |
| `airlock_add_file_reference` | `airlock.user.add_file_reference(...)` | Pin eligible upstream files for downstream validation. |
| `airlock_remove_file_reference` | `airlock.user.remove_file_reference(...)` | Remove a file reference pin. |

Workflow changes are lifecycle actions, not necessarily destructive. Tool
descriptions should say whether the operation is reversible under the configured
workflow.

### Attachment Tools

| Tool | Maps to | Purpose |
| --- | --- | --- |
| `airlock_add_attachment` | `airlock.user.add_attachment(...)` | Attach evidence to an existing file. |
| `airlock_replace_attachment` | `airlock.user.replace_attachment(...)` | Replace a logical attachment tag. |
| `airlock_delete_attachment` | `airlock.user.delete_attachment(...)` | Delete an attachment where allowed. |

Attachment replace/delete should be described as permanent in Airlock unless a
tested restore contract is added later.

### Expectation Tools

| Tool | Maps to | Purpose |
| --- | --- | --- |
| `airlock_list_expectations` | `airlock.admin.list_expectations(...)` or future user read procedure | Discover operational cadence/order contracts. |
| `airlock_describe_expectation` | `airlock.admin.describe_expectation(...)` | Inspect expectation clauses and scope. |
| `airlock_list_expectation_work` | `airlock.user.list_my_expectation_work(...)` | Show expectation status and required follow-up for the current user/role lens. |

Expectation administration should stay admin/spec-admin scoped. User-facing
expectation work/status discovery should use user procedures so agents do not
need admin scope for operational follow-up.

### Admin Tools

Admin tools should be disabled by default unless explicitly configured.

Suggested groups:

- roles and assignments
- specs, spec versions, templates, and template assignments
- references and reference access
- retention policies and outdated file cleanup
- expectations and expectation exceptions
- events/observability via `airlock.admin.list_events`
- billing status and billing logs where the caller has the right application
  role

Admin tools need stricter descriptions, explicit destructive flags, and full
structured return payloads because they affect governance, access, and audit.

## MCP Resources

Resources should be read-only and should call procedures behind the scenes
instead of querying owned tables directly.

Useful resources:

- `airlock://documentation/toc`
- `airlock://documentation/procedures`
- `airlock://documentation/section/{section_id}`
- `airlock://specs/{spec_name}/descriptor?role={airlock_role}`
- `airlock://specs/{spec_name}/files?role={airlock_role}`
- `airlock://events?since={timestamp}` for admin mode only

## MCP Prompts

Optional prompts can help agents behave consistently:

- `submit_file_to_airlock`: discover role/spec, describe spec, validate, load,
  attach, then report status.
- `draft_spec_from_template`: list assigned templates, create a draft spec, and
  ask an admin to review when publication is required.
- `triage_expectation_work`: list expectation work, inspect late/missing items,
  and suggest next procedure calls.
- `admin_safe_spec_change`: validate-only first, show impact, then alter only
  after explicit human approval.

Prompts should instruct agents to use installed documentation as source of truth.

## Input and Output Contracts

Each MCP tool should use JSON Schema for arguments. Schemas should be generated
or curated from Airlock procedure documentation, then tested against real calls.

Successful return shape:

```json
{
  "ok": true,
  "procedure": "airlock.user.load_data",
  "status": "loaded",
  "code": null,
  "message": "Loaded file.",
  "payload": {},
  "issues": [],
  "rows": []
}
```

Failure return shape:

```json
{
  "ok": false,
  "procedure": "airlock.user.load_data",
  "status": "error",
  "code": "ATTACHMENT_REQUIRED",
  "message": "Attachment required for this spec.",
  "issues": [
    {"code": "ATTACHMENT_REQUIRED", "message": "Provide attachment_content_base64.", "severity": "error"}
  ],
  "rows": []
}
```

Do not flatten Airlock outputs into prose-only summaries. Agents need reason
codes, issue arrays, returned file identifiers, path scopes, workflow states,
delegation context, and validation details.

## Common Agent Workflows

### Submit Data

```text
$airlock Submit @budget.csv to FY26 Budget Requests as role finadmin.
```

Expected behavior:

1. Identify role and spec.
2. Describe spec.
3. Validate file content.
4. Load only if valid.
5. Return loaded path/filename and workflow/attachment status.

### Submit Data with Attachment

```text
$airlock Submit this reimbursement CSV with @receipt.pdf as asmith.
```

Expected behavior:

1. Describe the reimbursement spec and attachment policy.
2. Validate the CSV.
3. Base64 encode the receipt only for the procedure call.
4. Load with `attachment_content_base64` and `attachment_filename`.
5. Do not log raw attachment bytes.

### Draft a Spec

```text
$airlock Draft a spec for weekly vendor invoices from the default template.
```

Expected behavior:

1. List assigned templates.
2. Describe the chosen template.
3. Prepare overrides.
4. Call create-from-template or admin create with `validate_only` first.
5. Ask before mutating.

### Triage Late Work

```text
$airlock Check expectation work for the finance specs.
```

Expected behavior:

1. List accessible expectations/work.
2. Explain late/missing/exception states.
3. Suggest the next Airlock procedure call, not direct table edits.

## Delegated Work

Delegation is for agent/API execution, not a Streamlit "acting as" mode. The
Streamlit UI may help humans create, view, and revoke grants. Bots and agent
tools perform delegated work through stored procedures.

Keep delegation mappings aligned with installed Airlock procedure names:
`airlock.user.create_delegation`, `airlock.user.list_my_delegations`, and the
trailing `on_behalf_of_user` / `delegation_id` parameters on delegated user
actions such as `load_data` and `add_attachment`.

When a human asks to set up their agent, use:

```sql
CALL airlock.user.create_delegation(...);
```

The current Snowflake user is always the principal. Do not pass a different
`principal_user`; the procedure rejects it. This prevents second-order
delegation.

Before delegated work, call:

```sql
CALL airlock.user.list_my_delegations('received');
```

Use `direction = 'received'` to discover grants where the current user is the
actor/delegate. Use `direction = 'granted'` to audit grants where another actor
may act for the current user. Use `include_inactive => TRUE` only when explaining
future, expired, or revoked delegations.

For active received rows:

- pass `PRINCIPAL_USER` as `on_behalf_of_user`
- pass `DELEGATION_ID` as `delegation_id`
- prefer structured `ACTION_CONTEXT` when available
- preserve actor, principal, and delegation id in output

Do not ask the agent to log in as the principal user.

Good:

```text
Submitted as Deb for Joe.
```

Bad:

```text
Joe submitted the file.
```

Preserve delegation denial codes such as `DELEGATION_NOT_FOUND`,
`DELEGATION_EXPIRED`, `DELEGATION_REVOKED`, `DELEGATION_PRINCIPAL_ACCESS_DENIED`,
or `AMBIGUOUS_DELEGATION`.

## Safety Rules

1. Default to read-only discovery unless a mutating tool is explicitly called.
2. For destructive tools, require explicit confirmation and target identifiers.
3. Prefer Airlock `validate_only` modes for declarative create/alter APIs.
4. Prefer Airlock `dry_run` modes for destructive operational previews.
5. Never bypass Airlock procedures to write stages or owned tables directly.
6. Log tool calls with procedure name, status, duration, and stable error code,
   but not secret values or file contents.
7. Keep file-content logging off by default.
8. Return authorization denials as denials; do not suggest privilege escalation
   unless the reason code clearly indicates the required admin action.
9. Preserve structured `ISSUES`, `VALIDATION`, `ACTION_CONTEXT`, and delegation
   payloads.

## Configuration

Suggested environment variables:

- `AIRLOCK_SNOWFLAKE_ACCOUNT`
- `AIRLOCK_SNOWFLAKE_USER`
- `AIRLOCK_SNOWFLAKE_ROLE`
- `AIRLOCK_SNOWFLAKE_WAREHOUSE`
- `AIRLOCK_APPLICATION_NAME`
- `AIRLOCK_PRIVATE_KEY_PATH`
- `AIRLOCK_PRIVATE_KEY_PASSPHRASE`
- `AIRLOCK_TOOLS_ADMIN_MODE=0|1`
- `AIRLOCK_DEFAULT_AIRLOCK_ROLE`
- `AIRLOCK_MAX_INLINE_BYTES`

The tool layer should also support named Snowflake connection profiles where
that is more convenient for local development.

## Optional Hook Guardrails

Some agent hosts can enforce hooks or policy checks around tool use. For Airlock
projects, consider hooks that:

- block direct writes to Airlock-owned tables and stages
- warn before `DROP`, `DELETE`, `TRUNCATE`, or broad `ALTER` outside approved
  Airlock procedures
- require `validate_only` before mutating spec/template procedures
- require `dry_run` before destructive operational procedures when available
- log procedure calls and result codes for supportability

Hooks should stay fast and conservative. If uncertain, prefer warning over
silently rewriting commands.

## MVP

A useful first version can be small:

1. Connect to Snowflake and report session/application context.
2. Fetch installed documentation and procedure registry.
3. List the caller's Airlock roles.
4. List and describe accessible specs.
5. Validate inline CSV.
6. Load inline CSV with optional attachment.
7. List files and select file data.
8. Add, replace, and delete attachments.
9. List and use received delegations for delegated procedure calls.
10. Provide stable structured errors and tests for common denial paths.

This MVP is enough for an agent to submit budget files, reimbursement files with
receipts, and other governed workflows without direct stage access.

## Later Phases

Phase 2:

- workflow work-item listing and workflow transitions
- file references / source-link operations
- reference data reads
- better file streaming for larger attachments

Phase 3:

- admin mode for spec/template/reference/retention/expectation management
- generated JSON Schemas from installed Airlock docs
- resource URIs for cached documentation and spec descriptors
- prompt templates for common Airlock workflows

Phase 4:

- optional hosted MCP server for teams
- OAuth or workload identity support where available
- observability dashboard for tool calls and Airlock procedure outcomes

## Testing

The tool layer should have:

- unit tests for JSON argument validation and procedure-call construction
- contract tests using fake Snowflake rows for output normalization
- integration tests against a demo Airlock install for discovery, validate, load,
  attach, list, select, workflow, delegation, and denial paths
- destructive-operation tests that prove `dry_run` and confirmation gates work
- documentation tests that compare the tool list to the installed procedure
  registry so stale tools are caught

The integration suite should stay focused. Prefer unit tests for schema and
mapping logic; use integration tests only for Snowflake session behavior,
procedure authorization, real file/attachment flow, installed-doc discovery, and
delegation enforcement.

## Skill Quality Checklist

- The description is specific enough that the agent loads it only for Airlock
  work.
- The first steps force installed-doc discovery.
- The skill never asks an agent to edit Airlock-owned tables/stages directly.
- The skill preserves structured procedure output.
- Destructive operations require approval or dry-run preview.
- Examples cover submit file, submit with attachment, draft spec, delegation,
  and expectation work.
- The skill can work with either SQL tools or an Airlock MCP server.
- The skill states how to handle common blockers: missing license seat, wrong
  Snowflake role, missing Airlock role, template not assigned, attachment
  required, delegation denied, access denied by workflow state.

## Distribution

Use Git when the skill should version alongside Airlock docs and examples. Use a
Snowflake stage or other internal artifact system when customers want
role-controlled distribution.

Recommended versioning:

- name the minimum Airlock API version expected
- include a compatibility note such as:
  `Requires Airlock API v1 procedures: documentation, list_my_roles,
  list_my_specs, describe_spec, validate_data, load_data`
- update the skill and examples in the same release pass as procedure contract
  changes

## Related Airlock Docs

- `docs/airlock_api_v1.md` for stored procedure contracts
- `docs/agent_delegation.md` for detailed delegation semantics
- `docs/procedure_cli_messaging.md` for deterministic agent-facing output
- `docs/ui_messaging_standards.md` for destructive/recovery language

## Open Product Questions

- Should admin and user MCP tools live in the same server with configuration
  gates, or in separate binaries?
- Should procedure schemas be generated at app build time, fetched from the
  installed app, or both?
- Should large files stream through the tool layer, require staged paths, or use
  signed upload flows?
- Should expectation read tools become user-facing, or remain admin/spec-admin
  only?
- Should managed-table specs get a separate tool group once that product shape is
  implemented?

## Rule of Thumb

If a tool or skill makes Airlock easier for an agent to use while preserving
stored procedures as the source of truth, it belongs. If it creates a second path
around Airlock permissions, validation, audit, billing, or lifecycle semantics,
it does not.

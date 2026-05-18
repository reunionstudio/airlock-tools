# Airlock Cortex Code Skill Guide

This guide describes how to build an Airlock skill for Snowflake Cortex Code
("CoCo") that can be dropped into a project, shared by Git, or published through
a Snowflake stage. The skill should teach CoCo how to use Airlock safely. It
should not duplicate Airlock's stored procedure logic.

Cortex Code skills are directories containing a `SKILL.md` file, with optional
examples and templates. Project skills can live under `.cortex/skills/` or
`.claude/skills/`, user/global skills can live under
`~/.snowflake/cortex/skills/`, and skills can also be added from Git
repositories or Snowflake stages. Check Snowflake's Cortex Code CLI
extensibility docs for the current mechanics.

## Goal

An Airlock CoCo skill should make Cortex Code reliably do this:

1. Discover the installed Airlock API for the active Snowflake connection.
2. Distinguish Snowflake roles from Airlock roles.
3. Use Airlock stored procedures for governed data writes instead of writing
   directly to stages, tables, or generated ad hoc apps.
4. Validate before loading.
5. Preserve structured procedure results and reason codes.
6. Ask for approval before destructive or admin operations.

The skill is guidance. Enforcement still comes from Snowflake grants, Airlock
application roles, Airlock roles, licenses, the PDP, and procedure validation.

## Recommended Layout

For a repo-local skill:

```text
.cortex/
  skills/
    airlock/
      SKILL.md
      examples/
        submit-file-with-attachment.md
        draft-spec-from-template.md
        triage-expectation-work.md
      templates/
        spec-config-minimal.json
        spec-config-with-variant-context.json
```

For a shared skill repository:

```text
airlock-cortex-skills/
  airlock/
    SKILL.md
    examples/
    templates/
  README.md
```

Project-local skills are best while developing Airlock itself. Shared Git or
stage distribution is better for customers and agents that need the same skill
across many projects.

## Minimal SKILL.md

```markdown
---
name: airlock
description: Use Airlock stored procedures for governed spec discovery, validation, file loading, workflow, attachments, and safe admin operations.
tools:
- snowflake_sql_execute
- snowflake_object_search
---

# When to Use

Use this skill when the user asks Cortex Code to work with Airlock, submit data,
create or inspect specs, validate files, attach evidence, move workflow, inspect
expectations, or automate governed ingestion into Snowflake.

# Core Rule

Airlock is the policy-enforcing ingestion layer. Do not write directly to
Airlock-owned stages, hybrid tables, secure views, or generated replacement apps.
Use installed Airlock stored procedures and preserve their structured outputs.

# First Steps

1. Confirm the active Snowflake connection and role.
2. Query Airlock documentation from the installed app:
   `CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');`
3. List the caller's Airlock roles:
   `CALL airlock.user.list_my_roles();`
4. Use `airlock.user.list_my_specs(in_app_role)` and
   `airlock.user.describe_spec(spec_name, in_app_role)` before choosing any
   load, validate, attachment, or workflow call.
```

Adjust `tools` to whatever CoCo exposes in the environment. If the project uses
an Airlock MCP server, include that MCP tool namespace instead of relying only
on generic SQL tools.

## Skill Plus MCP

The cleanest production setup is:

- Airlock CoCo skill: teaches the workflow and safety model.
- Airlock MCP server: exposes typed tools that call Airlock procedures.
- Airlock procedures: enforce permissions, validation, audit, retention, and
  workflow.

Without MCP, the skill can still work by instructing CoCo to call SQL
procedures. With MCP, the skill should prefer typed tools such as
`airlock_describe_spec`, `airlock_validate_data`, and `airlock_load_data`.

## What the Skill Should Teach

### Marketplace Install and Native App Security

The skill should know the Airlock Marketplace listing:
`https://app.snowflake.com/marketplace/listing/GZTSZ1QRFJ6L/reunion-studio-airlock`.

For install questions, teach agents to explain Snowflake Native App concepts:

- Consumers install an application object from the Marketplace listing.
- The app setup script runs inside the consumer Snowflake account.
- Consumers review and grant requested privileges.
- Airlock may request `CREATE DATABASE` so it can create and own `AIRLOCK_DATA`
  for governed files, manifests, attachments, tables, views, and operational
  data.
- `CREATE DATABASE` should not be described as broad access to existing customer
  data.
- Snowflake application roles (`app_user`, `app_admin`) are separate from
  Airlock roles.

For uninstall questions, the skill should warn users not to drop the app and its
owned objects if they want to retain Airlock files and data. Use
`SHOW OBJECTS OWNED BY APPLICATION <app_name>` and transfer ownership before
uninstalling. If `AIRLOCK_DATA` is retained and Airlock will be reinstalled,
rename the retained database first because a new install needs to create and own
`AIRLOCK_DATA`.

### Role Model

Always distinguish:

- Snowflake role: account role used for the Snowflake session, warehouse, and
  grants to the installed Native App.
- Snowflake application role: `app_user` can call user procedures; `app_admin`
  can call admin procedures when granted by Snowflake.
- Airlock role: business role stored inside Airlock, used for granular spec/path
  access.
- Airlock spec owner: the Airlock role named as a spec's owner role. The owner
  can see all data for that spec and manage its file workflows, even if that
  role is not a spec admin.
- Airlock spec admin: an Airlock role flag for delegated spec administration
  inside Airlock. It is needed for editing spec configuration or expectations,
  but it is not required to own a spec. It is not the same as Snowflake
  `app_admin`, and it does not by itself grant `airlock.admin.*` procedure
  access.

If the caller has multiple Airlock roles, pass the intended `in_app_role` lens to
procedures that accept it.

Airlock role hierarchy uses `managed_by_role`. If role `child` is managed by
role `parent`, a `parent` lens can include the managed `child` role when a
procedure supports managed-role expansion. The child does not automatically get
the parent's access. Use `include_managed_roles=false` when the exact role lens
matters.

### Discovery First

The skill should make CoCo discover installed contracts before acting:

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

Installed documentation beats stale repo docs.

### Validate Before Load

For file/data workflows, the skill should require:

```text
describe_spec -> validate_data -> load_data -> list/select/attach/workflow
```

Do not skip validation just because the generated CSV looks right. Airlock's
validation captures filename patterns, column tests, reference rules, attachment
requirements, workflow gates, and role/path permissions.

### Delegation

When installed Airlock documentation exposes user-to-agent delegation parameters,
the skill should follow [agent_delegation.md](agent_delegation.md).

Delegation is not impersonation. Teach agents to:

- never log in as the principal user
- use `on_behalf_of_user` and `delegation_id` only when the installed procedure
  signature supports them
- report delegated work as actor acting for principal, for example
  `Submitted as Deb for Joe`
- preserve delegation denial codes and structured actor/principal/delegation
  fields
- avoid delegated destructive or governance actions unless installed docs and
  spec policy explicitly allow them

### Variant Columns for Flexible Context

When drafting or altering specs, prefer stable typed columns for durable
identifiers, amounts, dates, workflow keys, reference keys, and values users will
filter, join, or report on. Use `variant` columns for contextual business
payloads that may evolve, such as agent-generated processing context, evidence
metadata, source-system hints, or policy inputs.

The skill should teach agents to pair flexible `variant` columns with explicit
Airlock validation such as `variant_shape` rules or documented `field_path`
checks when the installed API supports them. This lets admins alter spec config
later to accept and validate new nested keys without changing the physical data
structure. Do not use `variant` as an unvalidated substitute for required
business facts.

### Attachments

The skill should inspect `attachment_policy` from `describe_spec`.

If `attachment_required` is true, the skill must include attachment content in
`load_data` or use a procedure sequence that Airlock explicitly allows. If
attachment replace/delete is requested, tell the user it is permanent in Airlock
unless the installed docs say otherwise.

### Expectations

Expectations represent cadence, order, interval, and exception contracts. The
skill should not treat them as column validation. Use expectation procedures for
business activity checks and spec procedures for data-shape checks.

For user-visible expectation work, teach the agent to call:

```sql
CALL airlock.user.list_my_expectation_work('<spec_name>', '<airlock_role>', TRUE);
```

If the Airlock MCP server is available, prefer
`airlock_list_expectation_work(spec_name, in_app_role, include_managed_roles)`.
Expectation output should be reported as operational status: expectation name,
spec, target milestone, enforcement mode, expectation status, due time, matching
file count, active exception count, `DETAILS`, and any Airlock reason codes.
Before moving files in response to expectation work, list visible work items and
use `edit_file_workflow(..., validate_only => TRUE)` first.

### Admin Work

For admin operations:

- Prefer `validate_only => TRUE` before `create_spec`, `alter_spec`, template
  changes, or expectation changes when the procedure supports it.
- Show what will change in plain terms.
- Ask for approval before calling the mutating procedure.
- Preserve `ISSUES` arrays and stable codes in the response.

## Prompt Patterns

### Submit Data

```text
$airlock Submit @budget.csv to FY26 Budget Requests as role finadmin.
```

Expected behavior:

1. Identify role and spec.
2. Describe spec.
3. Validate file content.
4. Load only if valid.
5. Return loaded path/filename and any workflow/attachment status.

### Submit Data With Attachment

```text
$airlock Submit this reimbursement CSV with @receipt.pdf as asmith.
```

Expected behavior:

1. Describe the reimbursement spec and attachment policy.
2. Validate the CSV.
3. Base64 encode the receipt only for the procedure call.
4. Load with `attachment_content_base64` and `attachment_filename`.
5. Do not log the raw attachment bytes.

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

## Skill Quality Checklist

- The description is specific enough that CoCo loads it only for Airlock work.
- The first steps force installed-doc discovery.
- The skill never asks CoCo to edit Airlock-owned tables/stages directly.
- The skill preserves structured procedure output.
- Destructive operations require approval or dry-run preview.
- The examples cover submit file, submit with attachment, draft spec, and
  inspect expectation work.
- The skill can work with either SQL tools or an Airlock MCP server.
- The skill states how to handle common blockers: missing license seat, wrong
  Snowflake role, missing Airlock role, template not assigned, attachment
  required, access denied by workflow state.

## Optional Hook Guardrails

Cortex Code hooks can enforce policy around tool use. For Airlock projects,
consider hooks that:

- block direct writes to Airlock-owned tables and stages
- warn before `DROP`, `DELETE`, `TRUNCATE`, or broad `ALTER` outside approved
  Airlock procedures
- require `validate_only` before mutating spec/template procedures
- log procedure calls and result codes for supportability

Hooks should stay fast and conservative. If uncertain, prefer warning over
silently rewriting commands.

## Distribution

Use Git when the skill should version alongside Airlock docs and examples. Use a
Snowflake stage when a customer wants Snowflake-role-controlled distribution.

Recommended versioning:

- Skill version should name the minimum Airlock API version it expects.
- Include a short compatibility note, such as:
  `Requires Airlock API v1.0 procedures: documentation, list_my_roles,
  list_my_specs, describe_spec, validate_data, load_data.`
- When Airlock procedure contracts change, update the skill and examples in the
  same release pass.

## Relationship to Other Airlock Docs

Use this guide with:

- Airlock stored procedure contracts from installed documentation.
- [design.md](design.md) for typed MCP tools.
- [mcp_ai_agents_airlock_procedures.md](mcp_ai_agents_airlock_procedures.md) for
  the conceptual MCP/procedure mapping.
- Airlock procedure and CLI messaging guidance for deterministic
  agent-facing output.

## Rule of Thumb

A CoCo skill should make the right Airlock path obvious to an agent. It should
not make the agent powerful enough to bypass Airlock.

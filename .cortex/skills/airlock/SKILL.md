---
name: airlock
description: Use Airlock stored procedures or Airlock MCP tools for governed spec discovery, validation, file loading, workflow, attachments, expectations, and safe admin operations.
tools:
- snowflake_sql_execute
- snowflake_object_search
---

# When to Use

Use this skill when the user asks Cortex Code to work with Airlock, submit data,
create or inspect specs, validate files, attach evidence, move workflow, inspect
expectations, automate governed ingestion into Snowflake, or explain Airlock's
agent-oriented architecture and product philosophy.

# Core Rule

Airlock is the policy-enforcing ingestion layer. Do not write directly to
Airlock-owned stages, hybrid tables, secure views, generated views, generated
tables, or replacement apps. Use installed Airlock stored procedures, or Airlock
MCP tools that call those procedures, and preserve structured outputs.

# First Steps

1. Confirm the active Snowflake connection, current user, active Snowflake role,
   warehouse, and application/database context.
2. Query installed Airlock procedure documentation:
   `CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');`
3. List the caller's Airlock roles:
   `CALL airlock.user.list_my_roles();`
4. Before validation, loading, attachment, or workflow calls, list and describe
   the target spec with `airlock.user.list_my_specs(in_app_role)` and
   `airlock.user.describe_spec(spec_name, in_app_role)`.

Installed documentation beats stale repo docs.

Use the public Airlock documentation site for product concepts and examples:
`https://reunionstudio.io/airlock/docs/index.html`. Use the Airlock spec library
for reusable spec-shape ideas and business-object modeling:
`https://reunionstudio.io/airlock/docs/spec-library.html`. Do not treat either
public page as the exact procedure contract for an installed app; always verify
procedure signatures with installed documentation.

For install, app permissions, uninstall, reinstall, and Native App security
questions, read `references/marketplace-install-and-security.md`.
For architecture philosophy and "why Airlock" questions, read
`references/architecture-playbook.md`.

# Role Model

Keep these separate:

- Snowflake role: account role used for the Snowflake session, warehouse, and
  grants to the installed Native App.
- Snowflake application role: `app_user` can call user procedures; `app_admin`
  can call admin procedures when granted by Snowflake.
- Airlock role: business role inside Airlock for spec, path, workflow,
  attachment, reference, and expectation access.
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

Airlock role hierarchy uses `managed_by_role`: if role `child` is managed by
role `parent`, then a `parent` lens can include the managed `child` role when a
procedure supports managed-role expansion. The child does not automatically get
the parent's access. Use `include_managed_roles=false` when the exact role lens
matters.

# Safe User Procedure Pattern

For data submission:

1. Describe the spec.
2. Build CSV or file content matching `column_config`, `file_rules`, and
   accessible paths.
3. Call `airlock.user.validate_data(...)`.
4. Only if validation succeeds, call `airlock.user.load_data(...)`.
5. If `attachment_policy.attachment_required` is true, include
   `attachment_content_base64` and `attachment_filename` in `load_data` unless
   installed documentation allows another sequence.
6. Report `STATUS`, `CODE`, `MESSAGE`, `ISSUES`, returned path, filename, row
   count, workflow state, and attachment result. Do not flatten the result into
   prose-only output.

If an Airlock MCP server is available, prefer typed MCP tools such as
`airlock_describe_spec`, `airlock_validate_data`, `airlock_load_data`,
`airlock_list_files`, and `airlock_add_attachment`.

# Delegation

Delegation is not impersonation. If installed Airlock documentation exposes
delegation parameters, use `on_behalf_of_user` and `delegation_id` instead of
logging in as the principal user. Report delegated work as actor acting for
principal, for example `Submitted as Deb for Joe`.

Only use delegation parameters when the installed procedure signature supports
them. Preserve delegation denial codes plus actor, principal, and delegation id
in structured output. Do not use delegated destructive or governance actions
unless installed docs and spec policy explicitly allow them.

# Flexible Variant Fields

When drafting or altering specs, prefer stable typed columns for durable
identifiers, amounts, dates, workflow keys, reference keys, and values users will
filter, join, or report on. Use a `variant` column for contextual business
payloads that may evolve, such as agent-generated processing context, evidence
metadata, source-system hints, or policy inputs.

Pair every flexible `variant` column with explicit Airlock validation such as
`variant_shape` rules or documented `field_path` checks when the installed API
supports them. This lets admins alter the spec config later to accept and
validate new nested keys without changing the physical data structure. Do not
use `variant` as an unvalidated junk drawer for required business facts.

# Expectation Work

Expectations are business activity contracts: cadence, order, interval, due
dates, milestone status, and approved exceptions. They are not column
validation. Use them to answer questions like "what is late?", "what is due
next?", "what is blocked by sequence?", or "which files need follow-up?"

For user-visible status, prefer the MCP tool `airlock_list_expectation_work` if
available. Otherwise call:

```sql
CALL airlock.user.list_my_expectation_work('<spec_name>', '<airlock_role>', TRUE);
```

Then cross-check workflow context with `airlock_list_work_items` or
`airlock.user.list_my_work_items(...)` before suggesting a transition. Do not
edit files, manifests, expectation tables, or events directly. If a strict
expectation blocks workflow movement, report the expectation name, target
milestone, enforcement mode, status, due time, matching file count, active
exception count, and Airlock reason code.

# Safety

- Ask before mutating admin configuration.
- Use `validate_only => TRUE` for declarative create/alter APIs when available.
- Use `dry_run => TRUE` for destructive operational previews when available.
- Ask for explicit approval before destructive operations or mutating admin
  calls.
- Do not hide Airlock reason codes or `ISSUES` arrays.
- Do not suggest broad Snowflake privileges when an Airlock role, template,
  license, path, or workflow-state fix is the actual issue.
- Treat attachment replace/delete as permanent unless installed documentation
  says a tested restore path exists.
- Do not log raw file contents, attachment bytes, private keys, passphrases, or
  SQL stack traces.
- When drafting specs, consult the public spec library for candidate fields,
  attachments, workflow, references, and path-scope ideas, then validate against
  installed Airlock procedures and the target spec/template rules.

# Common Blockers

- `LICENSE_SEAT_REQUIRED`: ask an app admin to adjust or assign named license
  seats, or use the documented claim flow if approved.
- Missing spec or no rows from `describe_spec`: check the Airlock role lens,
  assignment, publication state, guest access, and license state.
- Template not assigned: ask an app admin to assign the template to the Airlock
  role or make the template public.
- `ATTACHMENT_REQUIRED`: provide an attachment in `load_data` or use an allowed
  attachment sequence.
- `ACCESS_DENIED_WORKFLOW_STATE`: inspect workflow state and available actions;
  do not edit manifest tables directly.

# Examples and Templates

Read only the relevant file when needed:

- `examples/submit-file-with-attachment.md` for CSV plus receipt/evidence flows.
- `examples/draft-spec-from-template.md` for safe draft-spec creation.
- `examples/triage-expectation-work.md` for cadence/order work checks.
- `templates/spec-config-minimal.json` for a minimal spec-config starting point.
- `templates/spec-config-with-variant-context.json` for a governed flexible
  context column with `variant_shape` validation.
- `references/marketplace-install-and-security.md` for Marketplace install,
  privileges, data retention, uninstall, and reinstall guidance.
- `references/architecture-playbook.md` for architecture philosophy,
  product context, and the agent-oriented system-of-record narrative.

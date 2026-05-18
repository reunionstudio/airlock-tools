# Airlock MCP Server Design

For the broader explanation of why an MCP adapter is useful, and why Airlock
stored procedures remain the source of truth, see
[mcp_ai_agents_airlock_procedures.md](mcp_ai_agents_airlock_procedures.md).
For Cortex Code skill packaging, see
[airlock_cortex_code_skill_guide.md](airlock_cortex_code_skill_guide.md).
For external MCP and Cortex Code benchmarks, see
[reference_benchmarks.md](reference_benchmarks.md).
For proposed user-to-agent delegation semantics, see
[agent_delegation.md](agent_delegation.md).

## Positioning

The MCP server is a transport adapter around Airlock stored procedures:

```text
MCP client
  -> Airlock MCP server
      -> Snowflake connector
          -> CALL airlock.user.* / airlock.admin.*
              -> Airlock procedures, PDP, events, owned storage
```

Examples assume the installed app object is named `airlock`; the server can use
`AIRLOCK_APPLICATION_NAME` when an account uses a different app name.

Authorization remains inside Snowflake and Airlock:

- Snowflake roles grant access to the Native App and procedures.
- Snowflake application roles are coarse procedure gates: `app_user` for
  `airlock.user.*`, and `app_admin` for `airlock.admin.*`.
- Airlock roles grant assignment-scoped access inside Airlock.
- A spec owner is the Airlock role named as a spec's owner role. Ownership gives
  that role full data visibility for the spec and workflow management ability,
  even when the role is not a spec admin.
- Airlock spec admin is an Airlock role flag for delegated spec management; it
  is needed to edit spec configuration or expectations, is not required for spec
  ownership, and is not the same as Snowflake `app_admin`.
- Airlock role hierarchy uses `managed_by_role`: the manager role can include
  managed child roles when a procedure supports managed-role expansion. The
  child does not automatically inherit the manager's access.
- License checks and procedure PDP checks remain the source of truth.
- Procedure output remains structured for agents.

The server must not query Airlock-owned hybrid tables, secure views, or stages
directly.

## Reference Benchmarks

Airlock Tools should be compatible with the patterns agents already see in
Snowflake and MCP ecosystems:

- Cortex Code skills are `SKILL.md` instruction packages with focused examples
  and optional tool configuration.
- Snowflake-managed MCP can expose generic stored procedure tools when direct
  procedure invocation is enough.
- This server adds Airlock-specific behavior: typed tool names, safe defaults,
  normalized structured results, resource URIs, prompts, and delegation-aware
  responses.
- Official MCP SDKs and reference servers are the benchmark for transport,
  registration, and boundary discipline.

The design goal is not to compete with generic Snowflake MCP. It is to make
Airlock's procedure surface easier for agents to use correctly.

## Documentation Sources

Use documentation in this order:

1. Installed Airlock docs from `airlock.user.documentation(...)` for the active
   app version's exact procedure contracts.
2. Public [Airlock docs](https://reunionstudio.io/airlock/docs/index.html) for
   conceptual guidance and operator workflows.
3. Public [Airlock spec library](https://reunionstudio.io/airlock/docs/spec-library.html)
   for spec modeling examples.

The public website should inform MCP prompts, skill examples, and product
language. It should not be used as the only source for procedure signatures or
return contracts.

In the agent-oriented architecture, Snowflake should be described as the direct
system of record for governed business outputs, not merely a downstream
analytics warehouse where data lands after a separate application creates the
official record.

When tools or prompts help users draft specs, they should recommend stable typed
columns for durable business facts and validated `variant` columns for evolving
context. `variant` fields should be governed with `variant_shape` or documented
`field_path` checks when supported, so flexibility stays inside the Airlock spec
contract.

Delegation support follows [agent_delegation.md](agent_delegation.md). The MCP
server exposes only the installed user-safe delegation contract:
`airlock.user.create_delegation`, `airlock.user.list_my_delegations`, and
delegated `load_data` / `add_attachment` parameters. Tool responses must
preserve actor user, principal user, and delegation id instead of summarizing
delegated work as direct user action.

## Install and Storage Permissions

Airlock is distributed through the Snowflake Marketplace listing:
[Reunion Studio Airlock](https://app.snowflake.com/marketplace/listing/GZTSZ1QRFJ6L/reunion-studio-airlock).

For install and security questions, distinguish Snowflake Native App platform
permissions from Airlock roles:

- Snowflake Native App install creates an application object in the consumer
  account and runs the app setup script.
- The consumer reviews and grants requested privileges to the application.
- Airlock may request `CREATE DATABASE` so it can create and own `AIRLOCK_DATA`
  for governed files, manifests, attachments, tables, views, and operational
  data.
- `CREATE DATABASE` is for Airlock's own storage database. It is not a request
  to read arbitrary existing customer databases.
- Snowflake application roles grant access to the app; Airlock roles enforce
  granular business access inside Airlock.

Uninstall guidance matters because Airlock stores customer files and data in
objects owned by the installed app. Before uninstalling, users who want to keep
that data should transfer ownership of app-owned objects, such as
`AIRLOCK_DATA`, to a customer-controlled role. If the retained database remains
named exactly `AIRLOCK_DATA`, a later reinstall cannot create and own a fresh
database with that same name; rename the retained database before reinstalling.

## MVP Tool Surface

Discovery:

- `airlock_get_connection_context`
- `airlock_get_api_info`
- `airlock_get_documentation`
- `airlock_list_my_roles`
- `airlock_check_license`

Delegation:

- `airlock_create_delegation`
- `airlock_list_my_delegations`

Spec discovery:

- `airlock_list_specs`
- `airlock_describe_spec`
- `airlock_select_reference_data`

Files and data:

- `airlock_validate_data`
- `airlock_load_data`
- `airlock_list_files`
- `airlock_select_files`
- `airlock_delete_files`

Workflow:

- `airlock_list_work_items`
- `airlock_edit_file_workflow`

Expectations:

- `airlock_list_expectation_work`

Attachments:

- `airlock_add_attachment`
- `airlock_replace_attachment`
- `airlock_delete_attachment`

## Messaging

Procedure output is normalized, not summarized away. The public response shape
uses `ok`, `procedure`, `status`, `code`, `message`, `payload`, `issues`, and
`rows`. Error messages are short and deterministic. Exceptions are sanitized and
logged without arguments, file contents, secrets, or stack traces.

## Later Phases

- File reference tools after the installed procedure signatures are available in
  structured documentation.
- Admin mode behind explicit configuration.
- Generated JSON schemas from installed procedure documentation.
- Larger file streaming or staged-path helpers.
- Integration tests against a demo Airlock install.

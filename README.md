# Airlock MCP Server

Airlock MCP is a thin Model Context Protocol server for Airlock's Snowflake stored
procedure API. It is designed for agents that need to discover specs, validate
CSV content, load governed files, inspect files, and manage attachments without
bypassing Airlock authorization, validation, workflow, or audit contracts.

The server calls documented `airlock.user.*` procedures. It does not query or
write Airlock-owned hybrid tables, secure views, or stages directly.

Documentation source priority:

1. Installed Airlock docs from `airlock.user.documentation(...)` for exact
   procedure contracts and the active app version.
2. The public [Airlock documentation site](https://reunionstudio.io/airlock/docs/index.html)
   for product concepts, guides, and operator-facing context.
3. The public [Airlock spec library](https://reunionstudio.io/airlock/docs/spec-library.html)
   for spec modeling examples and reusable business-object patterns.

Architecture premise: in an Airlock-oriented agent architecture, Snowflake is
the direct system of record for governed business outputs, not merely a
downstream analytics warehouse where data lands after another app creates the
official record.

Role boundaries:

- Snowflake roles and Snowflake application roles control the session and which
  installed app procedures can be called.
- Airlock roles control business access inside Airlock: specs, paths, workflow,
  attachments, references, and expectations.
- A spec owner is the Airlock role named as a spec's owner role. It can see all
  data for that spec and manage workflows, even when it is not a spec admin.
- Airlock spec admin is a delegated Airlock role capability for editing spec
  configuration or expectations. It is not required for spec ownership and is
  not the same thing as Snowflake `app_admin`.
- Airlock role hierarchy uses `managed_by_role`: a manager role can include
  managed child roles when procedures support managed-role expansion. The child
  does not automatically inherit the manager role's access.

Install and Native App setup:

- Airlock Marketplace listing:
  [Reunion Studio Airlock](https://app.snowflake.com/marketplace/listing/GZTSZ1QRFJ6L/reunion-studio-airlock).
- Airlock may request `CREATE DATABASE` so the Native App can create and own
  `AIRLOCK_DATA`, where it stores governed files, manifests, attachments,
  tables, views, and operational data.
- Before uninstalling Airlock, transfer ownership of app-owned objects that
  should be retained. Dropping the app with cascading deletion can delete
  app-owned files and data.
- If `AIRLOCK_DATA` is retained for archival use and Airlock will be reinstalled
  later, rename the retained database first. A fresh install needs to create and
  own a database named exactly `AIRLOCK_DATA`.

For background on how MCP relates to Airlock's database-native procedure API,
see [docs/mcp_ai_agents_airlock_procedures.md](docs/mcp_ai_agents_airlock_procedures.md).
For Snowflake Cortex Code skill guidance, see
[docs/airlock_cortex_code_skill_guide.md](docs/airlock_cortex_code_skill_guide.md)
and the repo-local skill under [.cortex/skills/airlock](.cortex/skills/airlock).
The skill also includes an Airlock architecture playbook reference for product
context and agent-oriented business architecture.
For maintenance checks after Airlock app upgrades, see the repo-local skill under
[.cortex/skills/airlock-tooling-maintenance](.cortex/skills/airlock-tooling-maintenance).
For proposed user-to-agent delegation semantics, see
[docs/agent_delegation.md](docs/agent_delegation.md). Delegation parameters are
not exposed by this MCP server until installed Airlock documentation exposes the
corresponding stored procedure contract.

## Status

This repository is a new public scaffold. The initial surface focuses on
user-safe workflows:

- Snowflake and Airlock context discovery.
- Installed Airlock documentation and procedure registry discovery.
- Airlock role and license checks.
- Spec listing and description.
- Inline CSV validation and loading.
- File listing, file selection, and guarded deletion previews.
- Workflow work item listing and validate-first workflow transitions.
- User-visible expectation work/status listing.
- File attachment add, replace, and delete.
- Read-only MCP resources and workflow prompts.

Admin tools are intentionally not exposed in this first cut. The code keeps the
boundary ready for explicit admin mode, but the MVP should be useful for normal
agent submission and review flows first.

Delegation is also intentionally not exposed in this first cut. When Airlock
ships delegated user-action parameters, the MCP server should preserve
`actor_user`, `principal_user`, and `delegation_id` in structured output and
avoid describing delegated work as direct user action.

## Install

```bash
uv sync --extra dev
```

or:

```bash
python -m pip install -e ".[dev]"
```

## Configure

Set Snowflake and Airlock settings in the environment used by your MCP client:

```bash
export AIRLOCK_SNOWFLAKE_ACCOUNT="org-account"
export AIRLOCK_SNOWFLAKE_USER="AIRLOCK_AGENT"
export AIRLOCK_SNOWFLAKE_ROLE="AIRLOCK_APP_USER_ROLE"
export AIRLOCK_SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export AIRLOCK_APPLICATION_NAME="AIRLOCK"
export AIRLOCK_PRIVATE_KEY_PATH="/path/to/rsa_key.p8"
export AIRLOCK_PRIVATE_KEY_PASSPHRASE="optional-passphrase"
```

For local development with Snowflake connector profiles, set:

```bash
export AIRLOCK_SNOWFLAKE_CONNECTION_NAME="airlock-dev"
```

Other useful settings:

```bash
export AIRLOCK_MCP_DEFAULT_AIRLOCK_ROLE="automation_user"
export AIRLOCK_MCP_MAX_INLINE_BYTES="1048576"
export AIRLOCK_MCP_ADMIN_TOOLS="0"
```

`AIRLOCK_SNOWFLAKE_PASSWORD` is also accepted for local development when your
account policy permits password authentication. Prefer key-pair authentication
for automation users.

## Run

```bash
uv run airlock-mcp
```

For MCP Inspector development:

```bash
uv run mcp dev src/airlock_mcp/server.py --with-editable .
```

## Tool Contract

Every Airlock procedure tool returns a consistent object:

```json
{
  "ok": true,
  "procedure": "airlock.user.load_data",
  "status": "ok",
  "code": null,
  "message": "Loaded file.",
  "payload": {},
  "issues": [],
  "rows": []
}
```

Procedure failures remain structured. The server preserves returned `STATUS`,
`CODE`, `MESSAGE`, `ISSUES`, identifiers, workflow state, validation details, and
result rows. Connector exceptions are sanitized to avoid leaking secrets, private
key paths, or stack traces.

## Safety Boundaries

- Read-only discovery is the default.
- `airlock_delete_files` defaults to `dry_run=true` and requires `confirm=true`
  before a mutating delete call.
- `airlock_edit_file_workflow` defaults to `validate_only=true`; set
  `validate_only=false` to apply the transition.
- Inline CSV and attachment payloads are capped by
  `AIRLOCK_MCP_MAX_INLINE_BYTES`.
- No tool grants broader access than the Snowflake user, active application role,
  Airlock roles, license state, and in-procedure PDP checks allow.

## Tests

```bash
uv run --extra dev pytest
```

The current tests cover procedure call construction, structured result
normalization, exception sanitization, and safety gate behavior.

## Design Notes

See [docs/design.md](docs/design.md) for the server boundary and MVP workflow
map. See [docs/mcp_ai_agents_airlock_procedures.md](docs/mcp_ai_agents_airlock_procedures.md)
for the conceptual MCP and agent integration overview.
See [docs/airlock_cortex_code_skill_guide.md](docs/airlock_cortex_code_skill_guide.md)
for the Cortex Code skill packaging guide.
Use [.cortex/skills/airlock-tooling-maintenance](.cortex/skills/airlock-tooling-maintenance)
to review installed Airlock API drift and decide whether this MCP server or the
skills need updates.

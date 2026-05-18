# Airlock Tools

Airlock Tools is a public toolkit for helping AI agents use Airlock safely. It
includes a thin Model Context Protocol server, Snowflake Cortex Code skills,
maintenance/drift guidance, and docs for working with Airlock's Snowflake stored
procedure API.

The MCP server component is designed for agents that need to discover specs,
validate CSV content, load governed files, inspect files, manage workflow, and
manage attachments without bypassing Airlock authorization, validation,
workflow, or audit contracts. It calls documented `airlock.user.*` procedures
and does not query or write Airlock-owned hybrid tables, secure views, or stages
directly.

Examples assume the installed app object is named `airlock`. If an account uses
a different app name, set `AIRLOCK_APPLICATION_NAME`.

The Cortex Code skill teaches agents the same safe workflow when they have
Snowflake SQL tools instead of MCP tools: discover installed docs, distinguish
Snowflake roles from Airlock roles, describe specs, validate before loading, and
preserve structured Airlock results.

## Quickstart

Choose the path that matches your agent environment:

- **MCP server**: use when Claude Desktop, Cursor, Codex, OpenClaw, or another
  MCP-compatible host should call typed Airlock tools. Start with
  [docs/quickstart-mcp.md](docs/quickstart-mcp.md).
- **Cortex Code skill**: use when Snowflake Cortex Code should call Airlock
  stored procedures directly through Snowflake SQL tools. Start with
  [docs/quickstart-cortex.md](docs/quickstart-cortex.md).
- **Both**: use the skill for Airlock workflow guidance and the MCP server for
  typed tool calls.

The first release is intended to be installed from GitHub and, after package
publication, run as a Python package named `airlock-tools`.

Documentation source priority:

1. Installed Airlock docs from `airlock.user.documentation(...)` for exact
   procedure contracts and the active app version.
2. The public [Airlock documentation site](https://reunionstudio.io/airlock/docs/index.html)
   for product concepts, guides, and operator-facing context.
3. The public [Airlock spec library](https://reunionstudio.io/airlock/docs/spec-library.html)
   for spec modeling examples and reusable business-object patterns.

For the upstream combined agent/tooling guide synced from Airlock, see
[docs/airlock-tools.md](docs/airlock-tools.md).

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
For MCP and Cortex Code examples used as benchmarks for this repo, see
[docs/reference_benchmarks.md](docs/reference_benchmarks.md).
For maintenance checks after Airlock app upgrades, see the repo-local skill under
[.cortex/skills/airlock-tooling-maintenance](.cortex/skills/airlock-tooling-maintenance).
For proposed user-to-agent delegation semantics, see
[docs/agent_delegation.md](docs/agent_delegation.md). The MCP server exposes the
current user-safe delegation surface from installed Airlock docs:
`airlock_create_delegation`, `airlock_list_my_delegations`, and delegated
`airlock_load_data` / `airlock_add_attachment` context.

## Status

This repository is a new public scaffold. The initial toolkit includes:

- A user-safe Airlock MCP server.
- A repo-local Airlock Cortex Code skill.
- A maintenance skill for detecting Airlock API drift.
- Snowflake CLI usage guidance.
- Design docs for MCP, CoCo skills, delegation, install/security, and
  agent-oriented Airlock architecture.

The initial MCP surface focuses on user-safe workflows:

- Snowflake and Airlock context discovery.
- Installed Airlock documentation and procedure registry discovery.
- Airlock role and license checks.
- Self-service delegation creation and delegation discovery.
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

Delegated load and attachment calls preserve Airlock's structured actor,
principal, and delegation context. The MCP server does not expose delegated
destructive or governance actions.

## Using the Toolkit

Use the pieces that match the agent environment:

- Use the MCP server when an agent host can call typed MCP tools.
- Use the Cortex Code skill when an agent has Snowflake SQL tools but not MCP.
- Use the maintenance skill to check whether a newer Airlock install changed
  procedure signatures, docs, delegation behavior, or expected agent workflows.
- Use the docs as agent-facing guidance, not as a replacement for installed
  Airlock documentation.

The MCP server is configured from the host environment or a named Snowflake
connection profile. Prefer key-pair authentication for automation users. See
[docs/quickstart-mcp.md](docs/quickstart-mcp.md) for consumer setup and
[docs/development.md](docs/development.md) for contributor commands and tests.

## Implementation Choice

The current MCP server is implemented in Python because Airlock is a
Snowflake-native product and Python has mature Snowflake connector support. MCP
does not require Python, though. A Node implementation would also be reasonable
if distribution through JavaScript package managers or a TypeScript-first agent
stack becomes more important.

The important contract is not the runtime. It is that tools remain thin wrappers
around documented Airlock stored procedures and preserve structured Airlock
results.

Snowflake-managed MCP can also expose Snowflake stored procedures as generic MCP
tools. Airlock Tools adds an Airlock-specific typed layer: safer defaults,
workflow prompts, resource naming, result normalization, delegation context, and
agent guidance for specs, roles, attachments, expectations, and workflow.

## Versioning

Use GitHub Releases and SemVer tags for this repo:

- Tag releases as `vMAJOR.MINOR.PATCH`, for example `v0.1.0`.
- Keep the Python package version in `pyproject.toml` and
  `src/airlock_mcp/__init__.py` aligned.
- Update [CHANGELOG.md](CHANGELOG.md) before tagging a release.
- During `0.x`, treat minor versions as meaningful feature releases and patch
  versions as bugfix/docs-only releases.
- Call out the minimum supported Airlock stored procedure API version when a
  release depends on a new installed Airlock contract.

The first public init commit should be tagged `v0.1.0` once the staged scaffold
is committed.

## Distribution

- GitHub is the source of truth for docs, skills, source, tests, and releases.
- GitHub Releases and tags provide stable install targets.
- The Python package name is `airlock-tools`; the MCP server command is
  `airlock-mcp` with `airlock-tools-mcp` as an alias.
- Cortex Code users can add the repo-local skills from `.cortex/skills` or from
  a released Git tag.
- Customer teams may publish the skill directory to a Snowflake stage when they
  want Snowflake-role-controlled distribution.
- Code, docs, skills, examples, and templates are licensed under Apache-2.0.

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

## Design Notes

See [docs/design.md](docs/design.md) for the server boundary and MVP workflow
map. See [docs/mcp_ai_agents_airlock_procedures.md](docs/mcp_ai_agents_airlock_procedures.md)
for the conceptual MCP and agent integration overview.
See [docs/airlock_cortex_code_skill_guide.md](docs/airlock_cortex_code_skill_guide.md)
for the Cortex Code skill packaging guide.
Use [.cortex/skills/airlock-tooling-maintenance](.cortex/skills/airlock-tooling-maintenance)
to review installed Airlock API drift and decide whether this MCP server or the
skills need updates.

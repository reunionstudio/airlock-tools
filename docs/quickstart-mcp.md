# MCP Server Quickstart

Use this path when your agent host can call MCP tools directly. The Airlock
Tools MCP server exposes typed Airlock tools that call documented
`airlock.user.*` stored procedures through Snowflake.

## Prerequisites

- Airlock is installed from the
  [Snowflake Marketplace listing](https://app.snowflake.com/marketplace/listing/GZTSZ1QRFJ6L/reunion-studio-airlock).
- The Snowflake user has a role that can use the installed Airlock app and
  activate the required Snowflake application role.
- The user has the required Airlock role assignment and license seat for the
  workflow.
- The agent host can pass Snowflake connection settings through environment
  variables or a Snowflake connector profile.

## Install

After the package is published for a release, run the server without a permanent
install:

```bash
uvx --from airlock-tools airlock-mcp
```

Equivalent command alias:

```bash
uvx --from airlock-tools airlock-tools-mcp
```

From a local clone:

```bash
uv run airlock-mcp
```

## Configure

Set connection values in the environment used by your MCP client:

```bash
export AIRLOCK_SNOWFLAKE_ACCOUNT="org-account"
export AIRLOCK_SNOWFLAKE_USER="AIRLOCK_AGENT"
export AIRLOCK_SNOWFLAKE_ROLE="AIRLOCK_APP_USER_ROLE"
export AIRLOCK_SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export AIRLOCK_APPLICATION_NAME="AIRLOCK"
export AIRLOCK_PRIVATE_KEY_PATH="/path/to/rsa_key.p8"
export AIRLOCK_PRIVATE_KEY_PASSPHRASE="optional-passphrase"
```

For local development, a named Snowflake connection profile can be simpler:

```bash
export AIRLOCK_SNOWFLAKE_CONNECTION_NAME="airlock-dev"
```

Optional Airlock settings:

```bash
export AIRLOCK_MCP_DEFAULT_AIRLOCK_ROLE="automation_user"
export AIRLOCK_MCP_MAX_INLINE_BYTES="1048576"
export AIRLOCK_MCP_ADMIN_TOOLS="0"
```

Prefer key-pair authentication for automation users. Password authentication is
accepted only when the Snowflake account policy allows it.

## MCP Client Example

For MCP clients that use JSON server configuration:

```json
{
  "mcpServers": {
    "airlock-tools": {
      "command": "uvx",
      "args": ["--from", "airlock-tools", "airlock-mcp"],
      "env": {
        "AIRLOCK_SNOWFLAKE_CONNECTION_NAME": "airlock-dev",
        "AIRLOCK_APPLICATION_NAME": "AIRLOCK",
        "AIRLOCK_MCP_ADMIN_TOOLS": "0"
      }
    }
  }
}
```

Keep secrets in the host's secret storage or environment. Do not commit private
keys, passwords, or passphrases into MCP configuration files.

## First Checks

After connecting, ask the agent to call read-only discovery tools first:

1. `airlock_get_connection_context`
2. `airlock_get_documentation` with `content_mode="PROCEDURES"`
3. `airlock_list_my_roles`
4. `airlock_list_specs`

Then use the normal Airlock pattern:

```text
describe_spec -> validate_data -> load_data -> list/select/workflow/attach
```

## Snowflake-Managed MCP Alternative

Snowflake-managed MCP can expose stored procedures as generic MCP tools. That
can be enough for teams that only need direct stored procedure invocation inside
Snowflake.

Use Airlock Tools MCP when agents need Airlock-specific tool names, safer
defaults, structured result normalization, prompts, resources, delegation
context, and guidance around specs, paths, workflow, expectations, and
attachments.

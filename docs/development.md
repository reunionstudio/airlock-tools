# Development

This page is for contributors working on the local Airlock Tools repo. General
users should start with the README, [quickstart-mcp.md](quickstart-mcp.md),
[quickstart-cortex.md](quickstart-cortex.md), and the installed Airlock
documentation.

## Install

```bash
uv sync --extra dev
```

Alternative editable install:

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

`AIRLOCK_SNOWFLAKE_PASSWORD` is accepted for local development when account
policy permits password authentication. Prefer key-pair authentication for
automation users.

## Run

```bash
uv run airlock-mcp
```

The package also exposes `airlock-tools-mcp` as an alias for the same server.

For MCP Inspector development:

```bash
uv run mcp dev src/airlock_mcp/server.py --with-editable .
```

## Verify

```bash
uv run --extra dev ruff check .
uv run --extra dev pytest
git diff --check
```

The current tests cover procedure call construction, structured result
normalization, exception sanitization, safety gates, and delegation argument
mapping.
